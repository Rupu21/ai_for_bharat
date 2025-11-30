# Design Document

## Overview

The Web Content Summarizer is a FastAPI-based web application that extracts, processes, and summarizes content from user-provided URLs. The system consists of a backend API built with FastAPI that handles URL validation, content fetching, text extraction, and summarization, paired with a frontend featuring a glassmorphic UI design. The application uses natural language processing techniques to generate summaries and extract key highlights from web content.

## Architecture

The application follows a layered architecture pattern:

1. **Presentation Layer**: HTML/CSS/JavaScript frontend with glassmorphic styling
2. **API Layer**: FastAPI endpoints for handling requests and responses
3. **Service Layer**: Business logic for content fetching, extraction, and summarization
4. **External Integration Layer**: HTTP client for fetching content from target websites

The system operates as follows:
- User submits a URL through the web interface
- Frontend sends POST request to FastAPI backend
- Backend validates URL, fetches content, extracts text, and generates summary
- Processed results are returned to frontend and displayed in glassmorphic UI

## Components and Interfaces

### 1. FastAPI Application (`main.py`)
- Serves static files (HTML, CSS, JS)
- Defines API endpoints
- Handles CORS configuration
- Manages application lifecycle

**Endpoints:**
- `GET /`: Serves the main HTML page
- `POST /api/summarize`: Accepts URL and returns summary with highlights

### 2. URL Validator (`validators.py`)
- Validates URL format using regex or urllib
- Checks for required URL components (scheme, netloc)

**Interface:**
```python
def validate_url(url: str) -> tuple[bool, str]:
    """
    Validates URL format.
    Returns: (is_valid, error_message)
    """
```

### 3. Content Fetcher (`fetcher.py`)
- Fetches HTML content from target websites
- Handles HTTP errors and timeouts
- Sets appropriate user agent headers

**Interface:**
```python
def fetch_content(url: str) -> tuple[str | None, str | None]:
    """
    Fetches HTML content from URL.
    Returns: (html_content, error_message)
    """
```

### 4. Text Extractor (`extractor.py`)
- Parses HTML using BeautifulSoup
- Extracts meaningful text content
- Removes scripts, styles, and navigation elements

**Interface:**
```python
def extract_text(html: str) -> str:
    """
    Extracts clean text from HTML content.
    Returns: Extracted text string
    """
```

### 5. Content Summarizer (`summarizer.py`)
- Generates summaries using AWS Bedrock with Claude 3.7 Sonnet
- Extracts key highlights using AI
- Handles edge cases (short content, empty content, API errors)
- Manages AWS Bedrock API communication

**Interface:**
```python
def generate_summary(text: str) -> tuple[str | None, str | None]:
    """
    Generates a summary from text content using AWS Bedrock.
    Returns: (summary_text, error_message)
    """

def extract_highlights(text: str) -> tuple[list[str] | None, str | None]:
    """
    Extracts key highlights from text using AWS Bedrock.
    Returns: (highlights_list, error_message)
    """
```

### 6. Frontend (`static/index.html`, `static/style.css`, `static/script.js`)
- Glassmorphic UI with input form
- JavaScript for form submission and API communication
- Dynamic display of results
- Loading states and error handling

## Data Models

### Request Model
```python
class SummarizeRequest(BaseModel):
    url: str
```

### Response Model
```python
class SummarizeResponse(BaseModel):
    success: bool
    url: str
    summary: str | None = None
    highlights: list[str] | None = None
    error: str | None = None
```

### Error Response Model
```python
class ErrorResponse(BaseModel):
    success: bool
    error: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Valid URL acceptance
*For any* valid URL format (with proper scheme and netloc), when submitted to the API, the system should accept it and return a successful response (not a validation error).
**Validates: Requirements 1.2**

### Property 2: Invalid URL rejection
*For any* invalid URL format (missing scheme, invalid characters, malformed structure), when submitted to the API, the system should reject it with an appropriate validation error message.
**Validates: Requirements 1.4**

### Property 3: Text extraction from HTML
*For any* HTML content, the text extraction function should return a non-empty string when the HTML contains text nodes, and the extracted text should not contain HTML tags.
**Validates: Requirements 2.4**

### Property 4: Summary generation and length
*For any* text content longer than a minimum threshold, the generated summary should be shorter than the original text and should be non-empty.
**Validates: Requirements 3.1, 3.4**

### Property 5: Highlights extraction as list
*For any* text content, when highlights are extracted, they should be returned as a list structure, and each highlight should be a non-empty string.
**Validates: Requirements 4.1, 4.2**

### Property 6: Highlights ordering consistency
*For any* text content, when highlights are extracted multiple times from the same content, they should maintain consistent ordering.
**Validates: Requirements 4.4**

### Property 7: Error recovery and form functionality
*For any* error response from the API, the frontend form should remain functional and allow submission of a new URL without page refresh.
**Validates: Requirements 7.4**

## Error Handling

The application implements comprehensive error handling at multiple levels:

### URL Validation Errors
- Empty URL: Return 400 with message "URL cannot be empty"
- Invalid format: Return 400 with message "Invalid URL format"
- Missing scheme: Return 400 with message "URL must include http:// or https://"

### Content Fetching Errors
- Network timeout: Return 500 with message "Unable to reach the website. Please check the URL and try again."
- HTTP error codes (4xx, 5xx): Return 500 with message "The website returned an error (status code: {code})"
- Connection refused: Return 500 with message "Connection to the website was refused"
- Blocked access: Return 500 with message "The website blocked automated access"

### Processing Errors
- Empty content: Return 200 with message in response indicating no content could be extracted
- Parsing errors: Return 500 with message "Failed to process website content"
- AWS Bedrock API errors: Return 500 with message "Failed to generate summary. Please try again."
- AWS authentication errors: Return 500 with message "Service configuration error. Please contact support."
- Content too long: Truncate content and retry, or return error if still fails
- Unexpected errors: Log full error, return 500 with generic message "An unexpected error occurred"

### Frontend Error Display
- Display errors in a dedicated error section with glassmorphic styling
- Clear previous results when showing errors
- Maintain form state to allow immediate retry

## Testing Strategy

The application will use a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage.

### Unit Testing

Unit tests will verify specific examples and integration points:

1. **URL Validation Examples**
   - Test specific valid URLs (http://example.com, https://example.com/path)
   - Test specific invalid URLs (missing scheme, invalid characters)
   - Test empty string handling

2. **API Endpoint Examples**
   - Test that GET / returns HTML page
   - Test that POST /api/summarize accepts requests
   - Test that required files exist (requirements.txt)

3. **Error Handling Examples**
   - Test specific error responses for known error conditions
   - Test that error messages are user-friendly

4. **Frontend Integration**
   - Test that HTML contains required input field
   - Test that summary appears in labeled section

### Property-Based Testing

Property-based tests will verify universal properties across many inputs using **Hypothesis** (Python's property-based testing library). Each test will run a minimum of 100 iterations.

1. **Property 1: Valid URL acceptance** (Requirements 1.2)
   - Generate random valid URLs with various schemes, domains, paths, and query parameters
   - Verify all are accepted by the validator
   - Tag: **Feature: web-content-summarizer, Property 1: Valid URL acceptance**

2. **Property 2: Invalid URL rejection** (Requirements 1.4)
   - Generate random invalid URLs (missing schemes, invalid characters, malformed)
   - Verify all are rejected with validation errors
   - Tag: **Feature: web-content-summarizer, Property 2: Invalid URL rejection**

3. **Property 3: Text extraction from HTML** (Requirements 2.4)
   - Generate random HTML documents with various structures
   - Verify extracted text contains no HTML tags
   - Verify non-empty HTML produces non-empty text
   - Tag: **Feature: web-content-summarizer, Property 3: Text extraction from HTML**

4. **Property 4: Summary generation and length** (Requirements 3.1, 3.4)
   - Generate random text content of varying lengths
   - Verify summaries are shorter than original text
   - Verify summaries are non-empty for sufficient input
   - Tag: **Feature: web-content-summarizer, Property 4: Summary generation and length**

5. **Property 5: Highlights extraction as list** (Requirements 4.1, 4.2)
   - Generate random text content
   - Verify highlights are returned as a list
   - Verify each highlight is a non-empty string
   - Tag: **Feature: web-content-summarizer, Property 5: Highlights extraction as list**

6. **Property 6: Highlights ordering consistency** (Requirements 4.4)
   - Generate random text content
   - Extract highlights multiple times
   - Verify ordering remains consistent across extractions
   - Tag: **Feature: web-content-summarizer, Property 6: Highlights ordering consistency**

7. **Property 7: Error recovery and form functionality** (Requirements 7.4)
   - Generate random error responses
   - Verify form remains functional after displaying errors
   - Verify new submissions work without page refresh
   - Tag: **Feature: web-content-summarizer, Property 7: Error recovery and form functionality**

### Test Organization

- Unit tests: `tests/test_*.py` files co-located with source
- Property tests: `tests/property_tests/test_properties.py`
- Frontend tests: `tests/test_frontend.py` using appropriate testing tools
- Integration tests: `tests/test_integration.py` for end-to-end flows

### Testing Tools

- **pytest**: Test runner and framework
- **Hypothesis**: Property-based testing library
- **httpx**: For testing FastAPI endpoints
- **BeautifulSoup**: For parsing test HTML in assertions

## Implementation Notes

### Summarization Approach

The application uses **AWS Bedrock with Claude 3.7 Sonnet** (`us.anthropic.claude-3-7-sonnet-20250219-v1:0`) for AI-powered summarization:
- Send extracted text content to Claude via AWS Bedrock API
- Request a concise summary and key highlights
- Use structured prompts to ensure consistent output format
- Handle API errors gracefully with fallback messages

**AWS Bedrock Configuration:**
- Model: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- Authentication: AWS CLI credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
- Region: Configurable via environment variable (default: us-east-1)
- Max tokens: Configurable (default: 1000)

This approach provides high-quality, abstractive summaries that understand context and meaning, rather than simple extractive summarization.

### Content Fetching Considerations

- Set reasonable timeout (10 seconds) for HTTP requests
- Use appropriate User-Agent header to avoid blocks
- Handle redirects automatically
- Limit response size to prevent memory issues

### Frontend Technology

- Vanilla JavaScript for simplicity (no framework required)
- CSS with backdrop-filter for glassmorphic effects
- Responsive design for various screen sizes
- Fetch API for backend communication

### Virtual Environment Setup

- Use Python 3.9+ for modern features
- Create requirements.txt with pinned versions including boto3 for AWS Bedrock
- Include setup instructions in README with AWS credentials configuration
- Use uvicorn as ASGI server for FastAPI
- Configure AWS credentials via environment variables or AWS CLI configuration

## Deployment Considerations

- Application runs locally via `uvicorn main:app --reload`
- Static files served from `/static` directory
- CORS configured for local development
- Environment variables for configuration (timeouts, limits)
