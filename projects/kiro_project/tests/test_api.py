"""Unit tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)


class TestRootEndpoint:
    """Test cases for GET / endpoint."""
    
    def test_get_root_returns_html(self):
        """Test that GET / serves HTML page."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
    
    def test_get_root_contains_title(self):
        """Test that the HTML page contains the application title."""
        response = client.get("/")
        content = response.text
        # Check for application title
        assert "web content summarizer" in content.lower()


class TestSummarizeEndpoint:
    """Test cases for POST /api/summarize endpoint."""
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    @patch('main.generate_summary')
    @patch('main.extract_highlights')
    def test_summarize_with_valid_request(
        self, 
        mock_highlights, 
        mock_summary, 
        mock_extract, 
        mock_fetch, 
        mock_validate
    ):
        """Test POST /api/summarize with valid request returns success."""
        # Mock all the processing steps
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body>Test content</body></html>", None)
        mock_extract.return_value = "Test content extracted"
        mock_summary.return_value = ("This is a summary", None)
        mock_highlights.return_value = (["Highlight 1", "Highlight 2"], None)
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == "https://example.com"
        assert data["summary"] == "This is a summary"
        assert data["highlights"] == ["Highlight 1", "Highlight 2"]
        assert data["error"] is None
    
    @patch('main.validate_url')
    def test_summarize_with_empty_url(self, mock_validate):
        """Test POST /api/summarize with empty URL returns validation error."""
        mock_validate.return_value = (False, "URL cannot be empty")
        
        response = client.post(
            "/api/summarize",
            json={"url": ""}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "URL cannot be empty" in data["detail"]
    
    @patch('main.validate_url')
    def test_summarize_with_invalid_url_format(self, mock_validate):
        """Test POST /api/summarize with invalid URL format returns error."""
        mock_validate.return_value = (False, "Invalid URL format")
        
        response = client.post(
            "/api/summarize",
            json={"url": "not-a-valid-url"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid URL format" in data["detail"]
    
    @patch('main.validate_url')
    def test_summarize_with_missing_scheme(self, mock_validate):
        """Test POST /api/summarize with URL missing scheme returns error."""
        mock_validate.return_value = (False, "URL must include http:// or https://")
        
        response = client.post(
            "/api/summarize",
            json={"url": "example.com"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "http://" in data["detail"] or "https://" in data["detail"]
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    def test_summarize_with_fetch_error(self, mock_fetch, mock_validate):
        """Test POST /api/summarize handles fetch errors."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = (None, "Unable to reach the website")
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://unreachable.example.com"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Unable to reach" in data["detail"]
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    def test_summarize_with_empty_content(self, mock_extract, mock_fetch, mock_validate):
        """Test POST /api/summarize handles empty extracted content."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body></body></html>", None)
        mock_extract.return_value = ""
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"] is None
        assert data["highlights"] is None
        assert "No content could be extracted" in data["error"]
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    @patch('main.generate_summary')
    def test_summarize_with_summary_generation_error(
        self, 
        mock_summary, 
        mock_extract, 
        mock_fetch, 
        mock_validate
    ):
        """Test POST /api/summarize handles summary generation errors."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body>Content</body></html>", None)
        mock_extract.return_value = "Some content"
        mock_summary.return_value = (None, "Failed to generate summary")
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate summary" in data["detail"]
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    @patch('main.generate_summary')
    @patch('main.extract_highlights')
    def test_summarize_with_highlights_extraction_error(
        self, 
        mock_highlights, 
        mock_summary, 
        mock_extract, 
        mock_fetch, 
        mock_validate
    ):
        """Test POST /api/summarize handles highlights extraction errors."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body>Content</body></html>", None)
        mock_extract.return_value = "Some content"
        mock_summary.return_value = ("Summary text", None)
        mock_highlights.return_value = (None, "Failed to extract highlights")
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to extract highlights" in data["detail"]
    
    def test_summarize_with_missing_url_field(self):
        """Test POST /api/summarize with missing URL field returns error."""
        response = client.post(
            "/api/summarize",
            json={}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_summarize_with_invalid_json(self):
        """Test POST /api/summarize with invalid JSON returns error."""
        response = client.post(
            "/api/summarize",
            data="not-json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    def test_summarize_with_whitespace_only_content(
        self, 
        mock_extract, 
        mock_fetch, 
        mock_validate
    ):
        """Test POST /api/summarize handles whitespace-only content."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body>   </body></html>", None)
        mock_extract.return_value = "   "
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"] is None
        assert data["highlights"] is None
        assert "No content could be extracted" in data["error"]


class TestResponseModels:
    """Test cases for response model structure."""
    
    @patch('main.validate_url')
    @patch('main.fetch_content')
    @patch('main.extract_text')
    @patch('main.generate_summary')
    @patch('main.extract_highlights')
    def test_successful_response_structure(
        self, 
        mock_highlights, 
        mock_summary, 
        mock_extract, 
        mock_fetch, 
        mock_validate
    ):
        """Test that successful response has correct structure."""
        mock_validate.return_value = (True, "")
        mock_fetch.return_value = ("<html><body>Test</body></html>", None)
        mock_extract.return_value = "Test content"
        mock_summary.return_value = ("Summary", None)
        mock_highlights.return_value = (["Point 1"], None)
        
        response = client.post(
            "/api/summarize",
            json={"url": "https://example.com"}
        )
        
        data = response.json()
        # Verify all expected fields are present
        assert "success" in data
        assert "url" in data
        assert "summary" in data
        assert "highlights" in data
        assert "error" in data
        
        # Verify types
        assert isinstance(data["success"], bool)
        assert isinstance(data["url"], str)
        assert isinstance(data["summary"], str) or data["summary"] is None
        assert isinstance(data["highlights"], list) or data["highlights"] is None
        assert isinstance(data["error"], str) or data["error"] is None
