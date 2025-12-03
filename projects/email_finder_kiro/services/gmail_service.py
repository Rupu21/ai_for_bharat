"""
Gmail Service for retrieving and parsing email data.

This module handles interaction with the Gmail API to retrieve unread emails
within a specified time range and parse them into structured Email objects.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.utils import parsedate_to_datetime

from models.data_models import Email


class GmailService:
    """
    Service for retrieving and parsing Gmail messages.
    
    This service provides methods to:
    - Query Gmail API for unread emails within a time range
    - Parse Gmail message format into Email objects
    - Handle Gmail API errors gracefully
    """
    
    def __init__(self, credentials: Credentials):
        """
        Initialize Gmail Service with authenticated credentials.
        
        Args:
            credentials: Google OAuth2 credentials with Gmail API access
            
        Raises:
            ValueError: If credentials are invalid or missing
        """
        if not credentials:
            raise ValueError("Valid credentials are required")
        
        if not credentials.valid:
            raise ValueError("Credentials must be valid and not expired")
        
        try:
            # Build Gmail API service
            self.service = build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            raise ValueError(f"Failed to initialize Gmail service: {str(e)}")
    
    def get_unread_emails(self, days_back: int) -> List[Email]:
        """
        Retrieves unread emails from the specified number of days back.
        
        Args:
            days_back: Number of days to look back for unread emails (positive integer)
            
        Returns:
            List[Email]: List of Email objects representing unread emails
            
        Raises:
            ValueError: If days_back is invalid
            RuntimeError: If Gmail API call fails
        """
        if days_back <= 0:
            raise ValueError("days_back must be a positive integer")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format date for Gmail query (YYYY/MM/DD)
        start_date_str = start_date.strftime('%Y/%m/%d')
        
        # Build Gmail query: unread emails after start_date
        query = f'is:unread after:{start_date_str}'
        
        try:
            # Call Gmail API to list messages with optimized limit
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Reduced for better performance
            ).execute()
            
            messages = results.get('messages', [])
            
            # If no messages found, return empty list
            if not messages:
                return []
            
            # Retrieve and parse each message with batch optimization
            emails = []
            for message in messages:
                try:
                    email_obj = self._get_and_parse_message(message['id'])
                    if email_obj:
                        emails.append(email_obj)
                except Exception as e:
                    # Log error but continue processing other emails
                    print(f"Warning: Failed to parse email {message['id']}: {str(e)}")
                    continue
            
            # Sort by timestamp (most recent first)
            emails.sort(key=lambda x: x.timestamp, reverse=True)
            
            return emails
            
        except HttpError as e:
            # Handle Gmail API specific errors
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            raise RuntimeError(
                f"Gmail API error: {error_details}. "
                "Please check your permissions and try again."
            )
        except Exception as e:
            # Handle other unexpected errors
            raise RuntimeError(
                f"Failed to retrieve emails: {str(e)}. "
                "Please try again later."
            )
    
    def _get_and_parse_message(self, message_id: str) -> Optional[Email]:
        """
        Retrieves and parses a single Gmail message.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Optional[Email]: Parsed Email object or None if parsing fails
        """
        try:
            # Get message with metadata format for faster retrieval
            # Only get full format if we need the body
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full',
                fields='id,snippet,payload(headers,body,parts)'  # Only fetch needed fields
            ).execute()
            
            return self.parse_email(message)
            
        except Exception as e:
            print(f"Error retrieving message {message_id}: {str(e)}")
            return None
    
    def parse_email(self, message: dict) -> Email:
        """
        Parses Gmail API message format into Email object.
        
        Args:
            message: Gmail API message dictionary
            
        Returns:
            Email: Parsed Email object
            
        Raises:
            ValueError: If message format is invalid or required fields are missing
        """
        if not message:
            raise ValueError("Message cannot be empty")
        
        try:
            # Extract message ID
            email_id = message.get('id', '')
            
            # Extract snippet
            snippet = message.get('snippet', '')
            
            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            subject = self._get_header(headers, 'Subject') or '(No Subject)'
            sender_full = self._get_header(headers, 'From') or 'Unknown'
            date_str = self._get_header(headers, 'Date')
            
            # Parse sender name and email
            sender, sender_email = self._parse_sender(sender_full)
            
            # Parse timestamp
            timestamp = self._parse_timestamp(date_str)
            
            # Extract email body
            body = self._extract_body(message.get('payload', {}))
            
            # Create Email object
            return Email(
                id=email_id,
                subject=subject,
                sender=sender,
                sender_email=sender_email,
                body=body,
                timestamp=timestamp,
                snippet=snippet
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse email: {str(e)}")
    
    def _get_header(self, headers: List[dict], name: str) -> Optional[str]:
        """
        Extracts a specific header value from Gmail headers list.
        
        Args:
            headers: List of header dictionaries
            name: Header name to find
            
        Returns:
            Optional[str]: Header value or None if not found
        """
        for header in headers:
            if header.get('name', '').lower() == name.lower():
                return header.get('value', '')
        return None
    
    def _parse_sender(self, sender_full: str) -> tuple[str, str]:
        """
        Parses sender string into name and email address.
        
        Args:
            sender_full: Full sender string (e.g., "John Doe <john@example.com>")
            
        Returns:
            tuple[str, str]: (sender_name, sender_email)
        """
        try:
            # Use email library to parse sender
            from email.utils import parseaddr
            name, email_addr = parseaddr(sender_full)
            
            # If no name, use email as name
            if not name:
                name = email_addr
            
            return name, email_addr
            
        except Exception:
            # Fallback: return full string as both name and email
            return sender_full, sender_full
    
    def _parse_timestamp(self, date_str: Optional[str]) -> datetime:
        """
        Parses email date string into datetime object.
        
        Args:
            date_str: Date string from email header
            
        Returns:
            datetime: Parsed datetime object
        """
        if not date_str:
            return datetime.now()
        
        try:
            # Use email.utils to parse RFC 2822 date format
            return parsedate_to_datetime(date_str)
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.now()
    
    def _extract_body(self, payload: dict) -> str:
        """
        Extracts email body text from Gmail message payload.
        
        Args:
            payload: Gmail message payload dictionary
            
        Returns:
            str: Email body text (plain text preferred, HTML as fallback)
        """
        body = ''
        
        # Check if payload has body data directly
        if 'body' in payload and 'data' in payload['body']:
            body = self._decode_body_data(payload['body']['data'])
            if body:
                return body
        
        # Check for multipart message
        if 'parts' in payload:
            body = self._extract_body_from_parts(payload['parts'])
        
        return body or '(No content)'
    
    def _extract_body_from_parts(self, parts: List[dict]) -> str:
        """
        Extracts body text from multipart message parts.
        
        Args:
            parts: List of message parts
            
        Returns:
            str: Extracted body text
        """
        plain_text = ''
        html_text = ''
        
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            # Recursively handle nested parts
            if 'parts' in part:
                nested_body = self._extract_body_from_parts(part['parts'])
                if nested_body:
                    return nested_body
            
            # Extract plain text
            if mime_type == 'text/plain' and 'body' in part and 'data' in part['body']:
                plain_text = self._decode_body_data(part['body']['data'])
            
            # Extract HTML as fallback
            elif mime_type == 'text/html' and 'body' in part and 'data' in part['body']:
                html_text = self._decode_body_data(part['body']['data'])
        
        # Prefer plain text over HTML
        return plain_text or html_text
    
    def _decode_body_data(self, data: str) -> str:
        """
        Decodes base64url encoded body data.
        
        Args:
            data: Base64url encoded string
            
        Returns:
            str: Decoded text
        """
        try:
            # Gmail uses base64url encoding (URL-safe base64)
            decoded_bytes = base64.urlsafe_b64decode(data)
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return ''
