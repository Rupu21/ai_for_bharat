"""
Configuration module for Email Insights Dashboard.

This module loads and validates all environment variables required for the application,
including Google OAuth, AWS Bedrock, logging, and application settings.

Requirements: 1.1, 5.1
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
import boto3
from google_auth_oauthlib.flow import Flow


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Config:
    """
    Central configuration class for Email Insights Dashboard.
    
    Loads and validates all environment variables on initialization.
    Provides typed access to configuration values and pre-configured clients.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration by loading environment variables.
        
        Args:
            env_file: Optional path to .env file. If None, uses default .env
            
        Raises:
            ConfigurationError: If required environment variables are missing
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        # Validate and load all configuration
        self._load_google_oauth_config()
        self._load_aws_config()
        self._load_app_config()
        self._load_logging_config()
        
        # Initialize clients
        self._bedrock_client = None
        self._oauth_flow = None
    
    def _load_google_oauth_config(self):
        """Load and validate Google OAuth configuration."""
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.google_redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        # Store missing variables for later validation
        self._oauth_missing = []
        if not self.google_client_id:
            self._oauth_missing.append('GOOGLE_CLIENT_ID')
        if not self.google_client_secret:
            self._oauth_missing.append('GOOGLE_CLIENT_SECRET')
        if not self.google_redirect_uri:
            self._oauth_missing.append('GOOGLE_REDIRECT_URI')
        
        # Gmail API scopes
        self.gmail_scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def _load_aws_config(self):
        """Load and validate AWS Bedrock configuration."""
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_session_token = os.getenv('AWS_SESSION_TOKEN')  # Support for temporary credentials
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Store missing variables for later validation
        self._aws_missing = []
        if not self.aws_access_key_id:
            self._aws_missing.append('AWS_ACCESS_KEY_ID')
        if not self.aws_secret_access_key:
            self._aws_missing.append('AWS_SECRET_ACCESS_KEY')
        # Note: AWS_SESSION_TOKEN is optional (only required for temporary credentials)
        
        # Bedrock model configuration
        self.bedrock_model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        self.bedrock_max_tokens = 4096
    
    def _load_app_config(self):
        """Load application-specific configuration."""
        self.session_secret_key = os.getenv('SESSION_SECRET_KEY')
        
        # Store missing variables for later validation
        self._app_missing = []
        if not self.session_secret_key:
            self._app_missing.append('SESSION_SECRET_KEY')
        
        # Optional application settings with defaults
        self.debug = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', '8000'))
    
    def _load_logging_config(self):
        """Load and configure logging settings."""
        self.log_file_path = os.getenv('LOG_FILE_PATH', 'logs/app.log')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Logging format configuration
        self.log_format = os.getenv(
            'LOG_FORMAT',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.log_date_format = os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    def get_bedrock_client(self):
        """
        Get or create AWS Bedrock client.
        
        Returns:
            boto3.client: Configured Bedrock runtime client
        """
        if self._bedrock_client is None:
            client_kwargs = {
                'service_name': 'bedrock-runtime',
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key,
                'region_name': self.aws_region
            }
            
            # Add session token if provided (for temporary credentials)
            if self.aws_session_token:
                client_kwargs['aws_session_token'] = self.aws_session_token
            
            self._bedrock_client = boto3.client(**client_kwargs)
        return self._bedrock_client
    
    def get_oauth_client_config(self) -> dict:
        """
        Get Google OAuth client configuration dictionary.
        
        Returns:
            dict: OAuth client configuration for google-auth-oauthlib
        """
        return {
            "web": {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.google_redirect_uri]
            }
        }
    
    def configure_logging(self):
        """
        Configure Python logging with settings from environment.
        
        This sets up the root logger with file handler and formatting.
        """
        # Get log level
        log_level = getattr(logging, self.log_level, logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=self.log_format,
            datefmt=self.log_date_format,
            handlers=[
                logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
    
    def validate(self, strict=True):
        """
        Validate that all required configuration is present and valid.
        
        Args:
            strict: If True, raises exception on missing config. If False, only warns.
        
        Raises:
            ConfigurationError: If any configuration is invalid (when strict=True)
        """
        # Check for missing required variables
        all_missing = []
        
        if hasattr(self, '_oauth_missing') and self._oauth_missing:
            all_missing.extend(self._oauth_missing)
        
        if hasattr(self, '_aws_missing') and self._aws_missing:
            all_missing.extend(self._aws_missing)
        
        if hasattr(self, '_app_missing') and self._app_missing:
            all_missing.extend(self._app_missing)
        
        if all_missing:
            error_msg = f"Missing required environment variables: {', '.join(all_missing)}"
            if strict:
                raise ConfigurationError(error_msg)
            else:
                print(f"Warning: {error_msg}")
                return
        
        # Test AWS credentials by attempting to create client (only if credentials exist)
        if not self._aws_missing:
            try:
                client = self.get_bedrock_client()
                # Optionally test connection (commented out to avoid unnecessary API calls)
                # client.list_foundation_models()
            except Exception as e:
                if strict:
                    raise ConfigurationError(f"Invalid AWS configuration: {str(e)}")
                else:
                    print(f"Warning: Invalid AWS configuration: {str(e)}")
        
        # Validate OAuth configuration format (only if credentials exist)
        if not self._oauth_missing:
            try:
                oauth_config = self.get_oauth_client_config()
                # Ensure all required fields are present
                assert oauth_config['web']['client_id']
                assert oauth_config['web']['client_secret']
                assert oauth_config['web']['redirect_uris']
            except Exception as e:
                if strict:
                    raise ConfigurationError(f"Invalid OAuth configuration: {str(e)}")
                else:
                    print(f"Warning: Invalid OAuth configuration: {str(e)}")
    
    def __repr__(self):
        """String representation of configuration (without sensitive data)."""
        return (
            f"Config("
            f"aws_region={self.aws_region}, "
            f"log_file={self.log_file_path}, "
            f"debug={self.debug}, "
            f"host={self.host}, "
            f"port={self.port}"
            f")"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config(env_file: Optional[str] = None, validate: bool = True, strict: bool = True) -> Config:
    """
    Get or create the global configuration instance.
    
    Args:
        env_file: Optional path to .env file
        validate: Whether to validate configuration
        strict: If True, raises exception on missing config. If False, only warns.
        
    Returns:
        Config: Global configuration instance
        
    Raises:
        ConfigurationError: If configuration is invalid (when strict=True)
    """
    global _config
    
    if _config is None:
        _config = Config(env_file)
        if validate:
            _config.validate(strict=strict)
    
    return _config


def reset_config():
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None
