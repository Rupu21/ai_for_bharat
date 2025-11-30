"""Unit tests for URL validation module."""

import pytest
from app.validators import validate_url


class TestValidateUrl:
    """Test cases for validate_url function."""
    
    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_with_path(self):
        """Test that URLs with paths are accepted."""
        is_valid, error = validate_url("https://example.com/path/to/page")
        assert is_valid is True
        assert error == ""
    
    def test_valid_url_with_query(self):
        """Test that URLs with query parameters are accepted."""
        is_valid, error = validate_url("https://example.com?param=value")
        assert is_valid is True
        assert error == ""
    
    def test_empty_url(self):
        """Test that empty URLs are rejected."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert error == "URL cannot be empty"
    
    def test_whitespace_only_url(self):
        """Test that whitespace-only URLs are rejected."""
        is_valid, error = validate_url("   ")
        assert is_valid is False
        assert error == "URL cannot be empty"
    
    def test_missing_scheme(self):
        """Test that URLs without scheme are rejected."""
        is_valid, error = validate_url("example.com")
        assert is_valid is False
        assert error == "URL must include http:// or https://"
    
    def test_invalid_scheme(self):
        """Test that URLs with invalid schemes are rejected."""
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert error == "URL must use http:// or https:// scheme"
    
    def test_url_with_spaces(self):
        """Test that URLs with spaces are rejected."""
        is_valid, error = validate_url("http://example .com")
        assert is_valid is False
        assert error == "Invalid URL format"
    
    def test_malformed_url(self):
        """Test that malformed URLs are rejected."""
        is_valid, error = validate_url("http://")
        assert is_valid is False
        assert error == "Invalid URL format"
