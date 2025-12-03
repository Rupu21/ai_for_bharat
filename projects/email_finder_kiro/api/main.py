"""
FastAPI application for Email Insights Dashboard.

This module defines the main FastAPI application with routes for
authentication, email analysis, and UI serving.
"""

import os
import uuid
from typing import Literal
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
import json
import asyncio
import re

from config import get_config, ConfigurationError
from services.auth_service import AuthenticationService
from services.gmail_service import GmailService
from services.analysis_engine import AnalysisEngine
from services.logging_service import LoggingService
from models.data_models import AnalysisMethod, AnalysisResult

# Configuration will be initialized lazily when services are created
# This allows tests to run without full environment setup
_config = None


def get_app_config():
    """Get or initialize application configuration."""
    global _config
    if _config is None:
        try:
            _config = get_config(validate=True, strict=True)
            _config.configure_logging()
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            print("Please check your .env file and ensure all required variables are set.")
            raise
    return _config


# Initialize FastAPI app
app = FastAPI(
    title="Email Insights Dashboard",
    description="Intelligent analysis of unread Gmail messages using LLM and NLP",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware for better performance
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure templates
templates = Jinja2Templates(directory="templates")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Service instances (initialized lazily with config)
_auth_service = None
_logging_service = None
_analysis_engine = None


def get_auth_service() -> AuthenticationService:
    """Get or create authentication service instance."""
    global _auth_service
    if _auth_service is None:
        config = get_app_config()
        _auth_service = AuthenticationService(config)
    return _auth_service


def get_logging_service() -> LoggingService:
    """Get or create logging service instance."""
    global _logging_service
    if _logging_service is None:
        config = get_app_config()
        _logging_service = LoggingService(config)
    return _logging_service


def get_analysis_engine() -> AnalysisEngine:
    """Get or create analysis engine instance."""
    global _analysis_engine
    if _analysis_engine is None:
        config = get_app_config()
        _analysis_engine = AnalysisEngine(config)
    return _analysis_engine


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text for safe JSON serialization.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        str: Sanitized text safe for JSON
    """
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    # Remove or replace problematic characters
    # Replace control characters except newline and tab
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Limit consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


# Pydantic models for request validation
class AnalyzeRequest(BaseModel):
    """Request model for email analysis endpoint."""
    
    days_back: int = Field(
        ...,
        gt=0,
        le=365,
        description="Number of days to look back for unread emails (1-365)"
    )
    method: Literal["llm", "nlp"] = Field(
        ...,
        description="Analysis method to use: 'llm' for LLM-based or 'nlp' for traditional NLP"
    )
    
    @field_validator('days_back')
    @classmethod
    def validate_days_back(cls, v):
        """Validate that days_back is a positive integer."""
        if v <= 0:
            raise ValueError('days_back must be a positive integer')
        if v > 365:
            raise ValueError('days_back cannot exceed 365 days')
        return v
    
    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        """Validate that method is either 'llm' or 'nlp'."""
        if v not in ['llm', 'nlp']:
            raise ValueError('method must be either "llm" or "nlp"')
        return v


class AnalyzeResponse(BaseModel):
    """Response model for email analysis endpoint."""
    
    summary: str
    important_emails: list
    total_unread: int
    analysis_method: str
    timestamp: str


class AuthStatusResponse(BaseModel):
    """Response model for authentication status endpoint."""
    
    authenticated: bool
    message: str


# Helper function to get or create session ID
def get_session_id(request: Request, response: Response) -> str:
    """
    Get existing session ID from cookie or create a new one.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        str: Session ID
    """
    session_id = request.cookies.get('session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key='session_id',
            value=session_id,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite='lax'
        )
    
    return session_id


# Authentication endpoints
@app.get("/auth/login")
async def login(response: Response):
    """
    Initiates OAuth2 authentication flow with Google Gmail.
    
    Returns:
        RedirectResponse: Redirects user to Google OAuth consent screen
        
    Raises:
        HTTPException: If OAuth flow initialization fails
    """
    try:
        auth_service = get_auth_service()
        logging_service = get_logging_service()
        
        # Generate authorization URL
        authorization_url = auth_service.initiate_oauth_flow()
        
        # Log the authentication attempt
        logging_service.log_input(
            user_id="anonymous",
            input_data={"action": "initiate_oauth"}
        )
        
        # Redirect to Google OAuth consent screen
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        get_logging_service().log_error(
            error=e,
            context={"endpoint": "/auth/login"}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate authentication: {str(e)}"
        )


@app.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str = None,
    error: str = None
):
    """
    Handles OAuth2 callback from Google and stores credentials.
    
    Args:
        request: FastAPI request object
        code: Authorization code from Google OAuth
        error: Error message if authentication failed
        
    Returns:
        RedirectResponse: Redirects to main dashboard with session cookie
        
    Raises:
        HTTPException: If callback handling fails
    """
    auth_service = get_auth_service()
    logging_service = get_logging_service()
    
    # Check for OAuth errors
    if error:
        logging_service.log_error(
            error=Exception(f"OAuth error: {error}"),
            context={"endpoint": "/auth/callback"}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Authentication failed: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code is required"
        )
    
    try:
        # Get existing session ID or create a new one
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Exchange authorization code for credentials
        credentials = auth_service.handle_oauth_callback(code, session_id)
        
        # Log successful authentication
        logging_service.log_input(
            user_id=session_id,
            input_data={
                "action": "oauth_callback_success",
                "has_credentials": credentials is not None
            }
        )
        
        # Create redirect response with session cookie
        redirect_response = RedirectResponse(url="/", status_code=302)
        redirect_response.set_cookie(
            key='session_id',
            value=session_id,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite='lax',
            secure=False  # Set to True in production with HTTPS
        )
        
        return redirect_response
        
    except Exception as e:
        logging_service.log_error(
            error=e,
            context={"endpoint": "/auth/callback", "code_present": code is not None}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete authentication: {str(e)}"
        )


@app.get("/auth/status", response_model=AuthStatusResponse)
async def auth_status(request: Request):
    """
    Checks the current authentication status.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthStatusResponse: Authentication status information
    """
    auth_service = get_auth_service()
    session_id = request.cookies.get('session_id')
    
    if not session_id:
        return AuthStatusResponse(
            authenticated=False,
            message="No active session"
        )
    
    # Check if session has valid credentials
    is_authenticated = auth_service.is_authenticated(session_id)
    
    return AuthStatusResponse(
        authenticated=is_authenticated,
        message="Authenticated" if is_authenticated else "Not authenticated"
    )


# Analysis endpoint with streaming progress
@app.post("/api/analyze")
async def analyze_emails(
    request: Request,
    analyze_request: AnalyzeRequest
):
    """
    Analyzes unread emails using the specified method with real-time progress updates.
    
    Args:
        request: FastAPI request object
        analyze_request: Analysis request parameters
        
    Returns:
        StreamingResponse: Server-sent events with progress updates and final results
        
    Raises:
        HTTPException: If user is not authenticated or analysis fails
    """
    auth_service = get_auth_service()
    logging_service = get_logging_service()
    analysis_engine = get_analysis_engine()
    
    # Get session ID
    session_id = request.cookies.get('session_id')
    
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in first."
        )
    
    # Get credentials from session
    credentials = auth_service.get_credentials(session_id)
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please log in again."
        )
    
    async def generate_progress():
        """Generator function for streaming progress updates."""
        try:
            # Send initial ping to establish connection
            yield ": ping\n\n"
            
            # Step 1: Connecting to Gmail
            yield f"data: {json.dumps({'step': 'connecting', 'message': 'Connecting to Gmail...'}, ensure_ascii=False)}\n\n"
            
            # Log the analysis request
            logging_service.log_input(
                user_id=session_id,
                input_data={
                    "days_back": analyze_request.days_back,
                    "method": analyze_request.method
                }
            )
            
            # Step 2: Retrieving emails
            yield f"data: {json.dumps({'step': 'retrieving', 'message': 'Retrieving unread emails...'}, ensure_ascii=False)}\n\n"
            
            # Initialize Gmail service with credentials
            gmail_service = GmailService(credentials)
            
            # Retrieve unread emails
            emails = gmail_service.get_unread_emails(analyze_request.days_back)
            
            # Step 3: Email count
            yield f"data: {json.dumps({'step': 'retrieved', 'message': f'Retrieved {len(emails)} unread emails', 'count': len(emails)}, ensure_ascii=False)}\n\n"
            
            # Log email retrieval
            logging_service.log_email_retrieval(
                user_id=session_id,
                count=len(emails),
                days_back=analyze_request.days_back
            )
            
            # Step 4: Analyzing
            method_name = "LLM (Claude)" if analyze_request.method == "llm" else "NLP"
            yield f"data: {json.dumps({'step': 'analyzing', 'message': f'Analyzing with {method_name}...'}, ensure_ascii=False)}\n\n"
            
            # Convert method string to AnalysisMethod enum
            analysis_method = AnalysisMethod.LLM if analyze_request.method == "llm" else AnalysisMethod.NLP
            
            # Analyze emails (this is the long-running operation)
            result = analysis_engine.analyze_emails(emails, analysis_method)
            
            # Log analysis output
            logging_service.log_output(
                user_id=session_id,
                output_data={
                    "total_unread": result.total_unread,
                    "important_count": len(result.important_emails),
                    "method": result.analysis_method
                },
                input_ref=f"analyze_{session_id}_{datetime.now().isoformat()}"
            )
            
            # Step 5: Complete - send results with sanitized data
            response_data = {
                'step': 'complete',
                'message': 'Analysis complete!',
                'result': {
                    'summary': sanitize_text(result.summary, 1000),
                    'important_emails': [
                        {
                            "email": {
                                "id": ie.email.id,
                                "subject": sanitize_text(ie.email.subject, 500),
                                "sender": sanitize_text(ie.email.sender, 200),
                                "sender_email": sanitize_text(ie.email.sender_email, 200),
                                "body": sanitize_text(ie.email.body, 5000),
                                "timestamp": ie.email.timestamp.isoformat(),
                                "snippet": sanitize_text(ie.email.snippet, 500)
                            },
                            "importance_score": ie.importance_score,
                            "reason": sanitize_text(ie.reason, 500)
                        }
                        for ie in result.important_emails
                    ],
                    'total_unread': result.total_unread,
                    'analysis_method': result.analysis_method,
                    'timestamp': result.timestamp.isoformat()
                }
            }
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            # Log the error
            logging_service.log_error(
                error=e,
                context={
                    "endpoint": "/api/analyze",
                    "days_back": analyze_request.days_back,
                    "method": analyze_request.method
                }
            )
            # Send error to client with sanitized message
            error_message = sanitize_text(str(e), 500)
            error_data = {
                'step': 'error',
                'message': error_message,
                'detail': f"Analysis failed: {error_message}"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
            "Content-Type": "text/event-stream; charset=utf-8"
        }
    )


# UI endpoint
@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    """
    Serves the main dashboard UI.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTMLResponse: Rendered HTML template
    """
    return templates.TemplateResponse(request, "index.html")


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    
    Logs configuration initialization and validates setup.
    """
    try:
        config = get_app_config()
        logging_service = get_logging_service()
        logging_service.log_input(
            user_id="system",
            input_data={
                "event": "application_startup",
                "config": str(config),
                "debug_mode": config.debug
            }
        )
    except ConfigurationError:
        # Configuration will be validated when services are actually used
        pass


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    try:
        logging_service = get_logging_service()
        logging_service.log_error(
            error=exc,
            context={"endpoint": request.url.path}
        )
    except:
        # If logging fails, continue without logging
        pass
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )
