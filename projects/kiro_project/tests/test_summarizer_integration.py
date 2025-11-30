"""Integration tests for summarizer module.

Note: These tests verify the module structure and basic functionality.
Actual AWS Bedrock API calls require valid credentials and are tested manually.
"""

import pytest
from app.summarizer import generate_summary, extract_highlights


def test_summarizer_functions_exist():
    """Test that required functions are available."""
    assert callable(generate_summary)
    assert callable(extract_highlights)


def test_generate_summary_returns_tuple():
    """Test that generate_summary returns a tuple."""
    result = generate_summary("Short text")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_extract_highlights_returns_tuple():
    """Test that extract_highlights returns a tuple."""
    result = extract_highlights("Short text")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_error_handling_structure():
    """Test that error responses follow expected structure."""
    # Empty content should return (None, error_message)
    summary, error = generate_summary("")
    assert summary is None
    assert isinstance(error, str)
    
    highlights, error = extract_highlights("")
    assert highlights is None
    assert isinstance(error, str)


def test_short_content_handling():
    """Test that short content is handled without API calls."""
    short_text = "This is a very short piece of text."
    
    # Should return content as-is for summary
    summary, error = generate_summary(short_text)
    assert summary == short_text
    assert error is None
    
    # Should return as single highlight
    highlights, error = extract_highlights(short_text)
    assert highlights == [short_text]
    assert error is None
