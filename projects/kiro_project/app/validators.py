"""URL validation module for Web Content Summarizer."""

from urllib.parse import urlparse


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validates URL format.
    
    Args:
        url: The URL string to validate
        
    Returns:
        A tuple of (is_valid, error_message) where:
        - is_valid: True if URL is valid, False otherwise
        - error_message: Empty string if valid, error description if invalid
    """
    # Check for empty URL
    if not url or not url.strip():
        return False, "URL cannot be empty"
    
    # Remove leading/trailing whitespace
    url = url.strip()
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Check if scheme exists and is http or https
        if not parsed.scheme:
            return False, "URL must include http:// or https://"
        
        if parsed.scheme not in ('http', 'https'):
            return False, "URL must use http:// or https:// scheme"
        
        # Check if netloc (domain) exists
        if not parsed.netloc:
            return False, "Invalid URL format"
        
        # Additional validation: check for invalid characters in netloc
        # netloc should not contain spaces or other invalid characters
        if ' ' in parsed.netloc:
            return False, "Invalid URL format"
        
        # URL is valid
        return True, ""
        
    except Exception:
        # If parsing fails for any reason, URL is invalid
        return False, "Invalid URL format"
