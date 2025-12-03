"""
Unit tests for FastAPI routes and request validation.

Tests the API endpoints, request validation, and error handling.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Set environment variables before importing app
os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test_client_secret'
os.environ['GOOGLE_REDIRECT_URI'] = 'http://localhost:8000/auth/callback'
os.environ['AWS_ACCESS_KEY_ID'] = 'test_aws_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_aws_secret'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['SESSION_SECRET_KEY'] = 'test_secret_key'
os.environ['LOG_FILE_PATH'] = 'logs/test.log'

from api.main import app
from models.data_models import Email, ImportantEmail, AnalysisResult, AnalysisMethod


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_credentials():
    """Create mock credentials."""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    return creds


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="test123",
        subject="Test Email",
        sender="Test Sender",
        sender_email="test@example.com",
        body="This is a test email body",
        timestamp=datetime.now(),
        snippet="This is a test..."
    )


@pytest.fixture
def sample_analysis_result(sample_email):
    """Create a sample analysis result."""
    important_email = ImportantEmail(
        email=sample_email,
        importance_score=0.85,
        reason="Contains urgent keywords"
    )
    
    return AnalysisResult(
        summary="Test summary of emails",
        important_emails=[important_email],
        total_unread=5,
        analysis_method="llm",
        timestamp=datetime.now()
    )


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_login_endpoint_exists(self, client):
        """Test that /auth/login endpoint is available."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log:
            mock_auth = Mock()
            mock_auth.initiate_oauth_flow.return_value = "https://accounts.google.com/o/oauth2/auth?test=true"
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            response = client.get("/auth/login", follow_redirects=False)
            assert response.status_code in [200, 302, 307]
    
    def test_login_initiates_oauth(self, client):
        """Test that login endpoint initiates OAuth flow."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log:
            mock_auth = Mock()
            mock_auth.initiate_oauth_flow.return_value = "https://accounts.google.com/o/oauth2/auth?test=true"
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            response = client.get("/auth/login", follow_redirects=False)
            mock_auth.initiate_oauth_flow.assert_called_once()
    
    def test_callback_endpoint_exists(self, client):
        """Test that /auth/callback endpoint is available."""
        response = client.get("/auth/callback?code=test_code")
        # Should not return 404
        assert response.status_code != 404
    
    def test_callback_requires_code(self, client):
        """Test that callback endpoint requires authorization code."""
        response = client.get("/auth/callback")
        assert response.status_code == 400
    
    def test_callback_handles_oauth_error(self, client):
        """Test that callback handles OAuth errors."""
        response = client.get("/auth/callback?error=access_denied")
        assert response.status_code == 400
        assert "access_denied" in response.json()["detail"]
    
    def test_auth_status_endpoint_exists(self, client):
        """Test that /auth/status endpoint is available."""
        response = client.get("/auth/status")
        assert response.status_code == 200
    
    def test_auth_status_returns_not_authenticated_without_session(self, client):
        """Test that auth status returns not authenticated without session."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False


class TestAnalyzeEndpoint:
    """Tests for the /api/analyze endpoint."""
    
    def test_analyze_endpoint_exists(self, client):
        """Test that /api/analyze endpoint is available."""
        response = client.post("/api/analyze", json={"days_back": 7, "method": "llm"})
        # Should not return 404
        assert response.status_code != 404
    
    def test_analyze_requires_authentication(self, client):
        """Test that analyze endpoint requires authentication."""
        response = client.post("/api/analyze", json={"days_back": 7, "method": "llm"})
        assert response.status_code == 401
    
    def test_analyze_validates_positive_days_back(self, client):
        """Test that days_back must be positive."""
        # Test with negative value
        response = client.post("/api/analyze", json={"days_back": -5, "method": "llm"})
        assert response.status_code == 422  # Validation error
        
        # Test with zero
        response = client.post("/api/analyze", json={"days_back": 0, "method": "llm"})
        assert response.status_code == 422
    
    def test_analyze_validates_days_back_maximum(self, client):
        """Test that days_back cannot exceed 365."""
        response = client.post("/api/analyze", json={"days_back": 400, "method": "llm"})
        assert response.status_code == 422
    
    def test_analyze_accepts_valid_days_back(self, client, mock_credentials, sample_analysis_result):
        """Test that valid days_back values are accepted."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log, \
             patch('api.main.get_analysis_engine') as mock_get_engine, \
             patch('api.main.GmailService') as mock_gmail:
            
            mock_auth = Mock()
            mock_auth.get_credentials.return_value = mock_credentials
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            mock_engine = Mock()
            mock_engine.analyze_emails.return_value = sample_analysis_result
            mock_get_engine.return_value = mock_engine
            
            mock_gmail_instance = Mock()
            mock_gmail_instance.get_unread_emails.return_value = []
            mock_gmail.return_value = mock_gmail_instance
            
            # Set session cookie
            client.cookies.set('session_id', 'test_session')
            
            response = client.post("/api/analyze", json={"days_back": 7, "method": "llm"})
            assert response.status_code == 200
    
    def test_analyze_validates_method_field(self, client):
        """Test that method must be 'llm' or 'nlp'."""
        response = client.post("/api/analyze", json={"days_back": 7, "method": "invalid"})
        assert response.status_code == 422
    
    def test_analyze_accepts_llm_method(self, client, mock_credentials, sample_analysis_result):
        """Test that 'llm' method is accepted."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log, \
             patch('api.main.get_analysis_engine') as mock_get_engine, \
             patch('api.main.GmailService') as mock_gmail:
            
            mock_auth = Mock()
            mock_auth.get_credentials.return_value = mock_credentials
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            mock_engine = Mock()
            mock_engine.analyze_emails.return_value = sample_analysis_result
            mock_get_engine.return_value = mock_engine
            
            mock_gmail_instance = Mock()
            mock_gmail_instance.get_unread_emails.return_value = []
            mock_gmail.return_value = mock_gmail_instance
            
            client.cookies.set('session_id', 'test_session')
            
            response = client.post("/api/analyze", json={"days_back": 7, "method": "llm"})
            assert response.status_code == 200
    
    def test_analyze_accepts_nlp_method(self, client, mock_credentials, sample_analysis_result):
        """Test that 'nlp' method is accepted."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log, \
             patch('api.main.get_analysis_engine') as mock_get_engine, \
             patch('api.main.GmailService') as mock_gmail:
            
            mock_auth = Mock()
            mock_auth.get_credentials.return_value = mock_credentials
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            mock_engine = Mock()
            mock_engine.analyze_emails.return_value = sample_analysis_result
            mock_get_engine.return_value = mock_engine
            
            mock_gmail_instance = Mock()
            mock_gmail_instance.get_unread_emails.return_value = []
            mock_gmail.return_value = mock_gmail_instance
            
            client.cookies.set('session_id', 'test_session')
            
            response = client.post("/api/analyze", json={"days_back": 7, "method": "nlp"})
            assert response.status_code == 200
    
    def test_analyze_requires_both_fields(self, client):
        """Test that both days_back and method are required."""
        # Missing method
        response = client.post("/api/analyze", json={"days_back": 7})
        assert response.status_code == 422
        
        # Missing days_back
        response = client.post("/api/analyze", json={"method": "llm"})
        assert response.status_code == 422
    
    def test_analyze_returns_analysis_result(self, client, mock_credentials, sample_analysis_result):
        """Test that analyze endpoint returns properly formatted result."""
        with patch('api.main.get_auth_service') as mock_get_auth, \
             patch('api.main.get_logging_service') as mock_get_log, \
             patch('api.main.get_analysis_engine') as mock_get_engine, \
             patch('api.main.GmailService') as mock_gmail:
            
            mock_auth = Mock()
            mock_auth.get_credentials.return_value = mock_credentials
            mock_get_auth.return_value = mock_auth
            mock_get_log.return_value = Mock()
            
            mock_engine = Mock()
            mock_engine.analyze_emails.return_value = sample_analysis_result
            mock_get_engine.return_value = mock_engine
            
            mock_gmail_instance = Mock()
            mock_gmail_instance.get_unread_emails.return_value = []
            mock_gmail.return_value = mock_gmail_instance
            
            client.cookies.set('session_id', 'test_session')
            
            response = client.post("/api/analyze", json={"days_back": 7, "method": "llm"})
            assert response.status_code == 200
            
            data = response.json()
            assert "summary" in data
            assert "important_emails" in data
            assert "total_unread" in data
            assert "analysis_method" in data
            assert "timestamp" in data


class TestUIEndpoint:
    """Tests for UI serving endpoint."""
    
    def test_root_endpoint_exists(self, client):
        """Test that / endpoint is available."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_html(self, client):
        """Test that / endpoint returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_root_contains_dashboard_title(self, client):
        """Test that / endpoint returns the dashboard HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Email Insights Dashboard" in response.text


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_endpoint_exists(self, client):
        """Test that /health endpoint is available."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self, client):
        """Test that health endpoint returns status."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestRequestValidation:
    """Tests for request validation with Pydantic models."""
    
    def test_rejects_non_integer_days_back(self, client):
        """Test that non-integer days_back is rejected."""
        response = client.post("/api/analyze", json={"days_back": "seven", "method": "llm"})
        assert response.status_code == 422
    
    def test_rejects_float_days_back(self, client):
        """Test that float days_back is rejected."""
        response = client.post("/api/analyze", json={"days_back": 7.5, "method": "llm"})
        assert response.status_code == 422
    
    def test_rejects_missing_request_body(self, client):
        """Test that missing request body is rejected."""
        response = client.post("/api/analyze")
        assert response.status_code == 422
    
    def test_rejects_empty_request_body(self, client):
        """Test that empty request body is rejected."""
        response = client.post("/api/analyze", json={})
        assert response.status_code == 422
