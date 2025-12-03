"""
Authentication Service for Gmail OAuth2 integration.

This module handles the OAuth2 authentication flow with Google Gmail API,
including credential storage, retrieval, and refresh operations.
"""

import os
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from config import get_config


class AuthenticationService:
    """
    Manages Gmail OAuth2 authentication and credential lifecycle.
    
    This service handles the complete OAuth2 flow including:
    - Initiating the authorization flow
    - Handling OAuth callbacks
    - Storing and retrieving credentials
    - Refreshing expired credentials
    """
    
    def __init__(self, config=None):
        """
        Initialize the authentication service with configuration.
        
        Args:
            config: Optional Config instance. If None, uses global config.
        """
        self.config = config or get_config()
        
        # OAuth configuration from centralized config
        self.client_id = self.config.google_client_id
        self.client_secret = self.config.google_client_secret
        self.redirect_uri = self.config.google_redirect_uri
        self.scopes = self.config.gmail_scopes
        
        # In-memory credential storage (session_id -> credentials)
        # In production, this should be replaced with Redis or database storage
        self._credential_store: Dict[str, Credentials] = {}
    
    def initiate_oauth_flow(self) -> str:
        """
        Initiates the OAuth2 authorization flow.
        
        Returns:
            str: Authorization URL for the user to visit and authenticate
            
        Raises:
            ValueError: If OAuth configuration is invalid
        """
        # Get OAuth client configuration from config
        client_config = self.config.get_oauth_client_config()
        
        # Create flow instance
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Request refresh token
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure refresh token
        )
        
        return authorization_url

    def handle_oauth_callback(self, code: str, session_id: str) -> Credentials:
        """
        Handles the OAuth2 callback and exchanges authorization code for credentials.
        
        Args:
            code: Authorization code received from Google OAuth callback
            session_id: Unique session identifier for storing credentials
            
        Returns:
            Credentials: Google OAuth2 credentials object
            
        Raises:
            ValueError: If the authorization code is invalid or exchange fails
        """
        if not code:
            raise ValueError("Authorization code is required")
        
        if not session_id:
            raise ValueError("Session ID is required")
        
        # Get OAuth client configuration from config
        client_config = self.config.get_oauth_client_config()
        
        # Create flow instance
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        try:
            # Exchange authorization code for credentials
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Store credentials in session storage
            self._credential_store[session_id] = credentials
            
            return credentials
            
        except Exception as e:
            raise ValueError(f"Failed to exchange authorization code: {str(e)}")
    
    def get_credentials(self, session_id: str) -> Optional[Credentials]:
        """
        Retrieves stored credentials for a given session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[Credentials]: Credentials object if found, None otherwise
        """
        if not session_id:
            return None
        
        credentials = self._credential_store.get(session_id)
        
        # Check if credentials exist and are valid
        if credentials:
            # If credentials are expired, try to refresh them
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials = self.refresh_credentials(credentials)
                    # Update stored credentials
                    self._credential_store[session_id] = credentials
                except Exception:
                    # If refresh fails, return None to trigger re-authentication
                    return None
        
        return credentials
    
    def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """
        Refreshes expired OAuth2 credentials.
        
        Args:
            credentials: Expired credentials object with refresh token
            
        Returns:
            Credentials: Refreshed credentials object
            
        Raises:
            ValueError: If credentials cannot be refreshed
        """
        if not credentials:
            raise ValueError("Credentials are required")
        
        if not credentials.refresh_token:
            raise ValueError("Refresh token is required to refresh credentials")
        
        try:
            # Use Google's Request object to refresh the token
            request = Request()
            credentials.refresh(request)
            return credentials
            
        except Exception as e:
            raise ValueError(f"Failed to refresh credentials: {str(e)}")
    
    def clear_credentials(self, session_id: str) -> bool:
        """
        Clears stored credentials for a session (logout).
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            bool: True if credentials were cleared, False if session not found
        """
        if session_id in self._credential_store:
            del self._credential_store[session_id]
            return True
        return False
    
    def is_authenticated(self, session_id: str) -> bool:
        """
        Checks if a session has valid credentials.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            bool: True if session has valid credentials, False otherwise
        """
        credentials = self.get_credentials(session_id)
        return credentials is not None and credentials.valid
