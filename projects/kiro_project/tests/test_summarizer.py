"""Tests for summarization module."""

import pytest
from app.summarizer import generate_summary, extract_highlights, _truncate_content


def test_truncate_content_short_text():
    """Test that short content is not truncated."""
    text = "Short content"
    result = _truncate_content(text, max_length=100)
    assert result == text


def test_truncate_content_long_text():
    """Test that long content is truncated."""
    text = "a" * 1000
    result = _truncate_content(text, max_length=100)
    assert len(result) <= 130  # 100 + truncation indicator
    assert "[content truncated]" in result


def test_generate_summary_empty_content():
    """Test handling of empty content."""
    summary, error = generate_summary("")
    assert summary is None
    assert error is not None
    assert "No content" in error


def test_generate_summary_short_content():
    """Test that very short content is returned as-is."""
    text = "This is short."
    summary, error = generate_summary(text)
    assert summary == text
    assert error is None


def test_extract_highlights_empty_content():
    """Test handling of empty content."""
    highlights, error = extract_highlights("")
    assert highlights is None
    assert error is not None
    assert "No content" in error


def test_extract_highlights_short_content():
    """Test that very short content returns single highlight."""
    text = "This is short."
    highlights, error = extract_highlights(text)
    assert highlights == [text]
    assert error is None


# Note: We don't test actual AWS Bedrock calls in unit tests
# Those would require mocking or integration tests with real credentials
# The actual API integration will be tested manually or with integration tests
