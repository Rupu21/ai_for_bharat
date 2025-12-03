"""
Unit tests for AuthenticationService.

Tests the OAuth2 authentication flow, credential management,
and session handling functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from google.oauth2.credentials import Credentials
from services.auth_service import AuthenticationService
from config import Config, reset_config


@pytest.fixture
def test_config():
    """Fixture to create a test configuration."""
    # Set all required environment variables for testing
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_client_secret'
    os.environ['GOOGLE_REDIRECT_URI'] = 'http://localhost:8000/auth/callback'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test_aws_key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_aws_secret'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['SESSION_SECRET_KEY'] = 'test_secret_key'
    os.environ['LOG_FILE_PATH'] = 'logs/test.log'
    
    # Reset global config
    reset_config()
    
    # Create config without validation
    config = Config()
    return config


@pytest.fixture
def auth_service(test_config):
    """Fixture to create an AuthenticationService instance with test configuration."""
    return AuthenticationService(test_config)


def test_auth_service_initialization(auth_service):
    """Test that AuthenticationService initializes correctly with environment variables."""
    assert auth_service.client_id == 'test_client_id'
    assert auth_service.client_secret == 'test_client_secret'
    assert auth_service.redirect_uri == 'http://localhost:8000/auth/callback'
    assert auth_service.scopes == ['https://www.googleapis.com/auth/gmail.readonly']


def test_auth_service_initialization_missing_env_vars():
    """Test that AuthenticationService raises error when environment variables are missing."""
    from config import ConfigurationError
    
    # Clear environment variables
    old_vars = {}
    for var in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI']:
        old_vars[var] = os.environ.pop(var, None)
    
    # Reset global config
    reset_config()
    
    try:
        # Creating config with missing OAuth vars should raise ConfigurationError when validated
        with pytest.raises(ConfigurationError, match="Missing required"):
            config = Config()
            config.validate(strict=True)
    finally:
        # Restore environment variables
        for var, value in old_vars.items():
            if value:
                os.environ[var] = value
        reset_config()


@patch('services.auth_service.Flow')
def test_initiate_oauth_flow(mock_flow_class, auth_service):
    """Test that initiate_oauth_flow generates a valid authorization URL."""
    # Mock the Flow instance
    mock_flow = Mock()
    mock_flow.authorization_url.return_value = (
        'https://accounts.google.com/o/oauth2/auth?client_id=test',
        'test_state'
    )
    mock_flow_class.from_client_config.return_value = mock_flow
    
    # Call the method
    auth_url = auth_service.initiate_oauth_flow()
    
    # Verify the authorization URL was generated
    assert auth_url == 'https://accounts.google.com/o/oauth2/auth?client_id=test'
    
    # Verify Flow was configured correctly
    mock_flow_class.from_client_config.assert_called_once()
    mock_flow.authorization_url.assert_called_once_with(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )


@patch('services.auth_service.Flow')
def test_handle_oauth_callback_success(mock_flow_class, auth_service):
    """Test successful OAuth callback handling and credential storage."""
    # Mock credentials
    mock_credentials = Mock(spec=Credentials)
    mock_credentials.token = 'test_access_token'
    mock_credentials.refresh_token = 'test_refresh_token'
    
    # Mock the Flow instance
    mock_flow = Mock()
    mock_flow.credentials = mock_credentials
    mock_flow_class.from_client_config.return_value = mock_flow
    
    # Call the method
    session_id = 'test_session_123'
    credentials = auth_service.handle_oauth_callback('test_auth_code', session_id)
    
    # Verify credentials were returned and stored
    assert credentials == mock_credentials
    assert auth_service._credential_store[session_id] == mock_credentials
    
    # Verify Flow was used correctly
    mock_flow.fetch_token.assert_called_once_with(code='test_auth_code')


def test_handle_oauth_callback_missing_code(auth_service):
    """Test that handle_oauth_callback raises error when code is missing."""
    with pytest.raises(ValueError, match="Authorization code is required"):
        auth_service.handle_oauth_callback('', 'test_session')


def test_handle_oauth_callback_missing_session_id(auth_service):
    """Test that handle_oauth_callback raises error when session_id is missing."""
    with pytest.raises(ValueError, match="Session ID is required"):
        auth_service.handle_oauth_callback('test_code', '')


def test_get_credentials_success(auth_service):
    """Test retrieving stored credentials for a valid session."""
    # Store mock credentials
    session_id = 'test_session_123'
    mock_credentials = Mock(spec=Credentials)
    mock_credentials.expired = False
    mock_credentials.valid = True
    auth_service._credential_store[session_id] = mock_credentials
    
    # Retrieve credentials
    credentials = auth_service.get_credentials(session_id)
    
    assert credentials == mock_credentials


def test_get_credentials_not_found(auth_service):
    """Test that get_credentials returns None for non-existent session."""
    credentials = auth_service.get_credentials('non_existent_session')
    assert credentials is None


def test_get_credentials_empty_session_id(auth_service):
    """Test that get_credentials returns None for empty session_id."""
    credentials = auth_service.get_credentials('')
    assert credentials is None


@patch('services.auth_service.Request')
def test_refresh_credentials_success(mock_request_class, auth_service):
    """Test successful credential refresh."""
    # Mock credentials with refresh token
    mock_credentials = Mock(spec=Credentials)
    mock_credentials.refresh_token = 'test_refresh_token'
    mock_credentials.expired = True
    
    # Mock the Request object
    mock_request = Mock()
    mock_request_class.return_value = mock_request
    
    # Call refresh
    refreshed = auth_service.refresh_credentials(mock_credentials)
    
    # Verify refresh was called
    mock_credentials.refresh.assert_called_once_with(mock_request)
    assert refreshed == mock_credentials


def test_refresh_credentials_no_refresh_token(auth_service):
    """Test that refresh_credentials raises error when refresh token is missing."""
    mock_credentials = Mock(spec=Credentials)
    mock_credentials.refresh_token = None
    
    with pytest.raises(ValueError, match="Refresh token is required"):
        auth_service.refresh_credentials(mock_credentials)


def test_refresh_credentials_none(auth_service):
    """Test that refresh_credentials raises error when credentials are None."""
    with pytest.raises(ValueError, match="Credentials are required"):
        auth_service.refresh_credentials(None)


def test_clear_credentials_success(auth_service):
    """Test clearing stored credentials."""
    session_id = 'test_session_123'
    mock_credentials = Mock(spec=Credentials)
    auth_service._credential_store[session_id] = mock_credentials
    
    # Clear credentials
    result = auth_service.clear_credentials(session_id)
    
    assert result is True
    assert session_id not in auth_service._credential_store


def test_clear_credentials_not_found(auth_service):
    """Test clearing credentials for non-existent session."""
    result = auth_service.clear_credentials('non_existent_session')
    assert result is False


def test_is_authenticated_valid_credentials(auth_service):
    """Test is_authenticated returns True for valid credentials."""
    session_id = 'test_session_123'
    mock_credentials = Mock(spec=Credentials)
    mock_credentials.expired = False
    mock_credentials.valid = True
    auth_service._credential_store[session_id] = mock_credentials
    
    assert auth_service.is_authenticated(session_id) is True


def test_is_authenticated_no_credentials(auth_service):
    """Test is_authenticated returns False when no credentials exist."""
    assert auth_service.is_authenticated('non_existent_session') is False
