"""Tests for text extraction module."""

import pytest
from app.extractor import extract_text


def test_extract_text_from_simple_html():
    """Test extracting text from simple HTML."""
    html = "<html><body><p>Hello world</p></body></html>"
    result = extract_text(html)
    assert "Hello world" in result
    assert "<p>" not in result
    assert "<body>" not in result


def test_extract_text_removes_scripts():
    """Test that script tags are removed."""
    html = """
    <html>
        <body>
            <script>alert('test');</script>
            <p>Visible content</p>
        </body>
    </html>
    """
    result = extract_text(html)
    assert "Visible content" in result
    assert "alert" not in result
    assert "script" not in result.lower()


def test_extract_text_removes_styles():
    """Test that style tags are removed."""
    html = """
    <html>
        <head><style>body { color: red; }</style></head>
        <body><p>Content here</p></body>
    </html>
    """
    result = extract_text(html)
    assert "Content here" in result
    assert "color: red" not in result


def test_extract_text_removes_navigation():
    """Test that navigation elements are removed."""
    html = """
    <html>
        <body>
            <nav><a href="#">Menu</a></nav>
            <p>Main content</p>
        </body>
    </html>
    """
    result = extract_text(html)
    assert "Main content" in result
    assert "Menu" not in result


def test_extract_text_handles_empty_html():
    """Test handling of empty HTML."""
    result = extract_text("")
    assert result == ""


def test_extract_text_handles_none():
    """Test handling of None input."""
    result = extract_text(None)
    assert result == ""


def test_extract_text_cleans_whitespace():
    """Test that extra whitespace is cleaned up."""
    html = """
    <html>
        <body>
            <p>Line   with    spaces</p>
            <p>Another line</p>
        </body>
    </html>
    """
    result = extract_text(html)
    assert "Line with spaces" in result
    assert "Another line" in result
    # Should not have excessive whitespace
    assert "   " not in result
