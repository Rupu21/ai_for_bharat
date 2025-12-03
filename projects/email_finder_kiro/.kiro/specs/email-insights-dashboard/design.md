# Design Document

## Overview

The Email Insights Dashboard is a FastAPI-based web application that provides intelligent analysis of unread Gmail messages. The system integrates with Gmail API for email retrieval, offers dual analysis modes (AWS Bedrock Claude LLM and traditional NLP), and presents results through a modern glassmorphic UI. The architecture emphasizes separation of concerns with distinct layers for authentication, data retrieval, analysis, presentation, and logging.

## Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (Frontend)                   │
│              Glassmorphic HTML/CSS/JavaScript            │
└─────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  API Layer (FastAPI)                     │
│         Routes, Request/Response Handling                │
└─────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ↓                       ↓
┌──────────────────────────┐  ┌──────────────────────────┐
│   Authentication Service  │  │    Analysis Service      │
│     (Gmail OAuth2)        │  │   (LLM/NLP Router)       │
└──────────────────────────┘  └──────────────────────────┘
                                         │
                            ┌────────────┴────────────┐
                            ↓                         ↓
                ┌──────────────────────┐  ┌──────────────────────┐
                │   LLM Processor      │  │   NLP Processor      │
                │  (AWS Bedrock)       │  │  (spaCy/NLTK)        │
                └──────────────────────┘  └──────────────────────┘
                            │
                            ↓
                ┌──────────────────────────┐
                │    Gmail Service         │
                │  (Email Retrieval)       │
                └──────────────────────────┘
                            │
                            ↓
                ┌──────────────────────────┐
                │    Logging Service       │
                │   (File/Database)        │
                └──────────────────────────┘
```

### Technology Stack

- **Backend Framework**: FastAPI (Python 3.9+)
- **Gmail Integration**: google-auth, google-auth-oauthlib, google-api-python-client
- **LLM Service**: AWS Bedrock (boto3) with Claude 3.7 Sonnet
- **NLP Libraries**: spaCy, NLTK, scikit-learn
- **Frontend**: HTML5, CSS3 (glassmorphism), Vanilla JavaScript
- **Logging**: Python logging module with file handlers
- **Configuration**: python-dotenv for environment variables

## Components and Interfaces

### 1. Authentication Module

**Responsibilities:**
- Handle Gmail OAuth2 flow
- Manage access tokens and refresh tokens
- Validate session state

**Interface:**
```python
class AuthenticationService:
    def initiate_oauth_flow(self) -> str:
        """Returns authorization URL for user to authenticate"""
        
    def handle_oauth_callback(self, code: str) -> Credentials:
        """Exchanges authorization code for credentials"""
        
    def get_credentials(self, session_id: str) -> Optional[Credentials]:
        """Retrieves stored credentials for session"""
        
    def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """Refreshes expired credentials"""
```

### 2. Gmail Service

**Responsibilities:**
- Retrieve unread emails within time range
- Parse email content and metadata
- Handle Gmail API errors

**Interface:**
```python
class GmailService:
    def __init__(self, credentials: Credentials):
        """Initialize with authenticated credentials"""
        
    def get_unread_emails(self, days_back: int) -> List[Email]:
        """Retrieves unread emails from specified days back"""
        
    def parse_email(self, message: dict) -> Email:
        """Parses Gmail API message into Email object"""
```

**Email Data Model:**
```python
@dataclass
class Email:
    id: str
    subject: str
    sender: str
    sender_email: str
    body: str
    timestamp: datetime
    snippet: str
```

### 3. Analysis Engine

**Responsibilities:**
- Route analysis requests to appropriate processor
- Coordinate analysis workflow
- Aggregate results

**Interface:**
```python
class AnalysisEngine:
    def analyze_emails(
        self, 
        emails: List[Email], 
        method: AnalysisMethod
    ) -> AnalysisResult:
        """Routes to LLM or NLP processor based on method"""
```

### 4. LLM Processor

**Responsibilities:**
- Format emails for Claude API
- Call AWS Bedrock with Claude 3.7 Sonnet
- Parse LLM responses into structured results

**Interface:**
```python
class LLMProcessor:
    def __init__(self, bedrock_client):
        """Initialize with AWS Bedrock client"""
        
    def process_emails(self, emails: List[Email]) -> AnalysisResult:
        """Analyzes emails using Claude LLM"""
        
    def _format_prompt(self, emails: List[Email]) -> str:
        """Creates prompt for LLM"""
        
    def _parse_response(self, response: str) -> AnalysisResult:
        """Parses LLM response into structured format"""
```

### 5. NLP Processor

**Responsibilities:**
- Extract keywords and entities from emails
- Calculate importance scores using heuristics
- Generate summaries using extractive methods

**Interface:**
```python
class NLPProcessor:
    def process_emails(self, emails: List[Email]) -> AnalysisResult:
        """Analyzes emails using traditional NLP"""
        
    def _extract_keywords(self, text: str) -> List[str]:
        """Extracts important keywords"""
        
    def _calculate_importance(self, email: Email) -> float:
        """Calculates importance score 0-1"""
        
    def _generate_summary(self, emails: List[Email]) -> str:
        """Creates extractive summary"""
```

**Importance Heuristics:**
- Sender domain (work vs personal)
- Keywords: urgent, important, deadline, action required
- Email length and structure
- Time sensitivity indicators

### 6. Logging Service

**Responsibilities:**
- Log all inputs and outputs with timestamps
- Record errors with context
- Provide structured logging format

**Interface:**
```python
class LoggingService:
    def log_input(self, user_id: str, input_data: dict):
        """Logs user input"""
        
    def log_output(self, user_id: str, output_data: dict, input_ref: str):
        """Logs system output"""
        
    def log_error(self, error: Exception, context: dict):
        """Logs errors with stack trace"""
        
    def log_email_retrieval(self, user_id: str, count: int, days_back: int):
        """Logs email retrieval operations"""
```

### 7. API Layer (FastAPI)

**Endpoints:**
```python
# Authentication
GET  /auth/login          # Initiates OAuth flow
GET  /auth/callback       # Handles OAuth callback
GET  /auth/status         # Checks authentication status

# Analysis
POST /api/analyze         # Triggers email analysis
  Body: {
    "days_back": int,
    "method": "llm" | "nlp"
  }
  Response: AnalysisResult

# UI
GET  /                    # Serves main dashboard
GET  /static/*            # Serves static assets
```

### 8. UI Component

**Responsibilities:**
- Render glassmorphic interface
- Handle user interactions
- Display analysis results

**Key UI Elements:**
- Authentication status indicator
- Days back input field (number)
- Analysis method selector (radio buttons: LLM/NLP)
- Analyze button
- Summary display panel
- Important emails list
- Loading states and error messages

## Data Models

### AnalysisResult
```python
@dataclass
class AnalysisResult:
    summary: str
    important_emails: List[ImportantEmail]
    total_unread: int
    analysis_method: str
    timestamp: datetime
```

### ImportantEmail
```python
@dataclass
class ImportantEmail:
    email: Email
    importance_score: float
    reason: str  # Why it's important
```

### AnalysisMethod
```python
class AnalysisMethod(Enum):
    LLM = "llm"
    NLP = "nlp"
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified several redundant properties:
- LLM and NLP processor output properties (5.2, 5.3, 5.4 and 6.2, 6.3, 6.4) can be consolidated since both processors must return the same structured format
- Routing properties (3.2, 3.3) can be combined into a single comprehensive routing property

### Correctness Properties

Property 1: Authentication credential storage
*For any* successful OAuth authentication response, the Authentication Module should store credentials that include an access token and can be retrieved using the session identifier
**Validates: Requirements 1.2**

Property 2: Authentication failure handling
*For any* authentication failure scenario, the Authentication Module should return an error message and prevent access to analysis endpoints
**Validates: Requirements 1.3**

Property 3: Valid time range acceptance
*For any* positive integer value for days back, the system should accept the value and use it to calculate the correct date range for email filtering
**Validates: Requirements 2.2**

Property 4: Invalid input rejection
*For any* invalid time range input (negative, zero, non-numeric, or excessively large values), the system should reject the input and display a validation error
**Validates: Requirements 2.3**

Property 5: Time range filtering accuracy
*For any* specified number of days back, the Gmail Service should retrieve only emails with timestamps within that range from the current date
**Validates: Requirements 2.4**

Property 6: Analysis method routing
*For any* analysis request with a specified method (LLM or NLP), the Analysis Engine should route the request to the corresponding processor
**Validates: Requirements 3.2, 3.3**

Property 7: Email query parameters
*For any* analysis initiation, the Gmail Service should construct a query that includes the unread status filter and the time range from the Time Range Filter
**Validates: Requirements 4.1**

Property 8: Email data completeness
*For any* email retrieved from Gmail API, the parsed Email object should contain non-empty values for subject, sender, body, and timestamp fields
**Validates: Requirements 4.2**

Property 9: Gmail API error handling
*For any* Gmail API error response, the Gmail Service should catch the error, log it, and return a user-friendly error message without crashing
**Validates: Requirements 4.4**

Property 10: LLM model specification
*For any* LLM processing request, the LLM Processor should invoke AWS Bedrock with the model ID "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
**Validates: Requirements 5.1**

Property 11: Analysis result structure
*For any* completed analysis (LLM or NLP), the returned AnalysisResult should contain a non-empty summary string, a list of important emails, the total unread count, and the analysis method used
**Validates: Requirements 5.4, 6.4**

Property 12: Result rendering completeness
*For any* AnalysisResult, the UI Component should render both the summary text and the list of important emails in the response HTML
**Validates: Requirements 7.2, 7.3**

Property 13: Input logging
*For any* user input (days back, analysis method selection), the Logging Service should create a log entry containing the input value, a timestamp, and a user identifier
**Validates: Requirements 8.1**

Property 14: Output logging
*For any* analysis output generated, the Logging Service should create a log entry containing the output data, a timestamp, and a reference to the associated input
**Validates: Requirements 8.2**

Property 15: Email retrieval logging
*For any* email retrieval operation, the Logging Service should create a log entry containing the count of emails retrieved and the time range used
**Validates: Requirements 8.3**

Property 16: Error logging
*For any* error that occurs in any component, the Logging Service should create a log entry containing the error message, stack trace, and contextual information
**Validates: Requirements 8.4**

Property 17: Log persistence
*For any* log entry written by the Logging Service, the entry should be retrievable from persistent storage after the write operation completes
**Validates: Requirements 8.5**

Property 18: API endpoint availability
*For any* running FastAPI application instance, the endpoints /auth/login, /auth/callback, /api/analyze, and / should return successful responses (not 404)
**Validates: Requirements 9.2, 9.3**

## Error Handling

### Authentication Errors
- **OAuth Failure**: Display user-friendly message, log error details, redirect to login
- **Token Expiration**: Automatically attempt refresh, prompt re-authentication if refresh fails
- **Invalid Credentials**: Clear session, redirect to login page

### Gmail API Errors
- **Rate Limiting**: Implement exponential backoff, inform user of delay
- **Network Errors**: Retry with timeout, display connection error message
- **Permission Denied**: Guide user to grant necessary Gmail permissions
- **Invalid Query**: Log error, return empty result set with explanation

### Analysis Errors
- **AWS Bedrock Errors**: Fall back to error message, suggest trying NLP method
- **Empty Email List**: Return result indicating no unread emails found
- **Malformed Email Content**: Skip problematic emails, log warning, continue with others
- **NLP Processing Errors**: Log error, return partial results if possible

### Validation Errors
- **Invalid Days Back**: Display inline error, prevent form submission
- **No Method Selected**: Highlight selection requirement, prevent analysis
- **Missing Authentication**: Redirect to login flow

### Logging Errors
- **Write Failures**: Attempt retry, log to stderr as fallback
- **Disk Space Issues**: Alert administrator, continue operation

## Testing Strategy

The Email Insights Dashboard will employ a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage.

### Unit Testing

Unit tests will verify specific examples, edge cases, and integration points:

**Authentication Module:**
- Test OAuth flow initiation returns valid authorization URL
- Test callback handling with valid authorization code
- Test session expiration detection
- Test credential refresh logic

**Gmail Service:**
- Test email parsing with sample Gmail API responses
- Test empty result handling
- Test date range calculation for specific dates
- Test error response handling

**Analysis Engine:**
- Test routing to LLM processor when method is "llm"
- Test routing to NLP processor when method is "nlp"

**LLM Processor:**
- Test prompt formatting with sample emails
- Test response parsing with mock Claude responses

**NLP Processor:**
- Test keyword extraction with sample texts
- Test importance scoring with known email patterns
- Test summary generation with sample email sets

**Logging Service:**
- Test log file creation
- Test log entry formatting
- Test error logging with sample exceptions

**API Layer:**
- Test endpoint responses with mock services
- Test request validation
- Test error response formatting

### Property-Based Testing

Property-based tests will verify universal properties across many randomly generated inputs using the **Hypothesis** library for Python.

**Configuration:**
- Each property-based test will run a minimum of 100 iterations
- Tests will use Hypothesis strategies to generate diverse test data
- Each test will be tagged with a comment referencing the design document property

**Test Coverage:**

Each correctness property listed above will be implemented as a single property-based test:

1. **Property 1 Test**: Generate random OAuth responses, verify credential storage and retrieval
2. **Property 2 Test**: Generate various authentication failure scenarios, verify error handling
3. **Property 3 Test**: Generate random positive integers, verify acceptance and date calculation
4. **Property 4 Test**: Generate invalid inputs (negative, zero, strings, floats), verify rejection
5. **Property 5 Test**: Generate random day values, verify email timestamp filtering
6. **Property 6 Test**: Generate random method selections, verify correct processor routing
7. **Property 7 Test**: Generate random time ranges, verify query parameter construction
8. **Property 8 Test**: Generate random Gmail API responses, verify all required fields present
9. **Property 9 Test**: Generate various API errors, verify graceful handling
10. **Property 10 Test**: Generate random email sets, verify correct model ID in all Bedrock calls
11. **Property 11 Test**: Generate random analysis results, verify structure completeness
12. **Property 12 Test**: Generate random AnalysisResults, verify both summary and important emails rendered
13. **Property 13 Test**: Generate random user inputs, verify logging with required fields
14. **Property 14 Test**: Generate random outputs, verify logging with timestamp and input reference
15. **Property 15 Test**: Generate random retrieval operations, verify logging of count and range
16. **Property 16 Test**: Generate various error types, verify logging with stack trace
17. **Property 17 Test**: Generate random log entries, verify persistence and retrieval
18. **Property 18 Test**: Verify all required endpoints return non-404 responses

**Hypothesis Strategies:**
- `st.integers(min_value=1, max_value=365)` for valid days back
- `st.one_of(st.integers(max_value=0), st.text(), st.floats())` for invalid inputs
- `st.lists(st.builds(Email, ...))` for email collections
- `st.sampled_from([AnalysisMethod.LLM, AnalysisMethod.NLP])` for method selection
- Custom strategies for OAuth responses, Gmail API responses, and error scenarios

### Integration Testing

While not part of the core property-based testing strategy, integration tests will verify:
- End-to-end OAuth flow with Google
- Gmail API integration with test account
- AWS Bedrock API calls with actual service
- Complete analysis workflow from authentication to result display

### Test Organization

```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_gmail_service.py
│   ├── test_analysis_engine.py
│   ├── test_llm_processor.py
│   ├── test_nlp_processor.py
│   ├── test_logging_service.py
│   └── test_api.py
├── property/
│   ├── test_auth_properties.py
│   ├── test_gmail_properties.py
│   ├── test_analysis_properties.py
│   ├── test_logging_properties.py
│   └── test_api_properties.py
└── integration/
    ├── test_oauth_flow.py
    ├── test_gmail_integration.py
    └── test_end_to_end.py
```

## Security Considerations

- **Credential Storage**: OAuth tokens stored in secure session storage, never in logs
- **API Keys**: AWS credentials managed via environment variables, never committed to code
- **Input Validation**: All user inputs sanitized to prevent injection attacks
- **HTTPS**: All external API calls use HTTPS
- **Scope Limitation**: Gmail OAuth scope limited to read-only access
- **Session Management**: Sessions expire after inactivity, require re-authentication

## Performance Considerations

- **Email Batch Processing**: Process emails in batches to avoid memory issues with large result sets
- **LLM Rate Limiting**: Implement request throttling for AWS Bedrock to stay within quotas
- **Caching**: Cache Gmail API responses for short duration to reduce API calls during development
- **Async Processing**: Use FastAPI's async capabilities for I/O-bound operations
- **Timeout Handling**: Set reasonable timeouts for all external API calls

## Deployment Considerations

- **Environment Variables**: Required variables include:
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
  - `SESSION_SECRET_KEY`
  - `LOG_FILE_PATH`
- **Dependencies**: Install via `requirements.txt` with pinned versions
- **Database**: Optional database for session storage in production (Redis recommended)
- **Logging**: Configure log rotation to prevent disk space issues
- **Monitoring**: Implement health check endpoint for uptime monitoring
