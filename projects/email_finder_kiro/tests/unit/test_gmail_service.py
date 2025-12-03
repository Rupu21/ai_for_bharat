"""
Unit tests for Gmail Service.

Tests the core functionality of the GmailService class including
email retrieval, parsing, and error handling.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from google.oauth2.credentials import Credentials

from services.gmail_service import GmailService
from models.data_models import Email


class TestGmailServiceInitialization:
    """Tests for GmailService initialization."""
    
    def test_init_with_valid_credentials(self):
        """Test that GmailService initializes with valid credentials."""
        # Create mock credentials
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            assert service is not None
            mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    
    def test_init_with_none_credentials(self):
        """Test that GmailService raises error with None credentials."""
        with pytest.raises(ValueError, match="Valid credentials are required"):
            GmailService(None)
    
    def test_init_with_invalid_credentials(self):
        """Test that GmailService raises error with invalid credentials."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = False
        
        with pytest.raises(ValueError, match="Credentials must be valid"):
            GmailService(mock_creds)


class TestGetUnreadEmails:
    """Tests for get_unread_emails method."""
    
    def test_get_unread_emails_with_invalid_days_back(self):
        """Test that get_unread_emails rejects invalid days_back values."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            # Test zero
            with pytest.raises(ValueError, match="days_back must be a positive integer"):
                service.get_unread_emails(0)
            
            # Test negative
            with pytest.raises(ValueError, match="days_back must be a positive integer"):
                service.get_unread_emails(-5)
    
    def test_get_unread_emails_returns_empty_list_when_no_messages(self):
        """Test that get_unread_emails returns empty list when no messages found."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            # Mock the API call chain
            mock_service.users().messages().list().execute.return_value = {}
            
            service = GmailService(mock_creds)
            emails = service.get_unread_emails(7)
            
            assert emails == []
    
    def test_get_unread_emails_constructs_correct_query(self):
        """Test that get_unread_emails constructs the correct Gmail query."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            # Mock the API call chain
            mock_list = Mock()
            mock_service.users().messages().list.return_value = mock_list
            mock_list.execute.return_value = {}
            
            service = GmailService(mock_creds)
            service.get_unread_emails(7)
            
            # Verify the query includes 'is:unread' and 'after:' with date
            call_args = mock_service.users().messages().list.call_args
            query = call_args[1]['q']
            
            assert 'is:unread' in query
            assert 'after:' in query


class TestParseEmail:
    """Tests for parse_email method."""
    
    def test_parse_email_with_complete_message(self):
        """Test parsing a complete Gmail message."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            # Create a sample Gmail message
            message = {
                'id': '12345',
                'snippet': 'This is a test email',
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Test Subject'},
                        {'name': 'From', 'value': 'John Doe <john@example.com>'},
                        {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
                    ],
                    'body': {
                        'data': 'VGhpcyBpcyB0aGUgZW1haWwgYm9keQ=='  # Base64: "This is the email body"
                    }
                }
            }
            
            email = service.parse_email(message)
            
            assert email.id == '12345'
            assert email.subject == 'Test Subject'
            assert email.sender == 'John Doe'
            assert email.sender_email == 'john@example.com'
            assert email.snippet == 'This is a test email'
            assert 'This is the email body' in email.body
            assert isinstance(email.timestamp, datetime)
    
    def test_parse_email_with_missing_subject(self):
        """Test parsing email with missing subject."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            message = {
                'id': '12345',
                'snippet': 'Test',
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'test@example.com'},
                        {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
                    ],
                    'body': {'data': 'dGVzdA=='}
                }
            }
            
            email = service.parse_email(message)
            assert email.subject == '(No Subject)'
    
    def test_parse_email_with_empty_message(self):
        """Test that parse_email raises error with empty message."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            with pytest.raises(ValueError, match="Message cannot be empty"):
                service.parse_email(None)
    
    def test_parse_sender_with_name_and_email(self):
        """Test parsing sender with both name and email."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            name, email = service._parse_sender('John Doe <john@example.com>')
            assert name == 'John Doe'
            assert email == 'john@example.com'
    
    def test_parse_sender_with_email_only(self):
        """Test parsing sender with email only."""
        mock_creds = Mock(spec=Credentials)
        mock_creds.valid = True
        
        with patch('services.gmail_service.build') as mock_build:
            mock_build.return_value = Mock()
            service = GmailService(mock_creds)
            
            name, email = service._parse_sender('john@example.com')
            assert name == 'john@example.com'
            assert email == 'john@example.com'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
