# Implementation Plan

- [x] 1. Set up project structure and dependencies



  - Create FastAPI project directory structure with folders for services, models, api, static, and templates
  - Create requirements.txt with FastAPI, google-auth, google-api-python-client, boto3, spacy, nltk, hypothesis, pytest
  - Create .env.example file documenting required environment variables
  - Initialize Python virtual environment and install dependencies
  - _Requirements: 9.1_

- [x] 2. Implement core data models





  - Create Email dataclass with id, subject, sender, sender_email, body, timestamp, snippet fields
  - Create AnalysisResult dataclass with summary, important_emails, total_unread, analysis_method, timestamp fields
  - Create ImportantEmail dataclass with email, importance_score, reason fields
  - Create AnalysisMethod enum with LLM and NLP values
  - _Requirements: 5.4, 6.4_

- [ ]* 2.1 Write property test for data model structure
  - **Property 11: Analysis result structure**
  - **Validates: Requirements 5.4, 6.4**

- [x] 3. Implement Authentication Module





  - Create AuthenticationService class with OAuth2 flow methods
  - Implement initiate_oauth_flow() to generate Google authorization URL
  - Implement handle_oauth_callback() to exchange code for credentials
  - Implement get_credentials() and refresh_credentials() for session management
  - Store credentials in session storage with session_id as key
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 3.1 Write property test for credential storage
  - **Property 1: Authentication credential storage**
  - **Validates: Requirements 1.2**

- [ ]* 3.2 Write property test for authentication failure handling
  - **Property 2: Authentication failure handling**
  - **Validates: Requirements 1.3**

- [x] 4. Implement Gmail Service





  - Create GmailService class that accepts credentials in constructor
  - Implement get_unread_emails() to query Gmail API with date range filter
  - Calculate date range from days_back parameter using datetime operations
  - Implement parse_email() to extract subject, sender, body, timestamp from Gmail message format
  - Handle Gmail API errors with try-except blocks and user-friendly error messages
  - _Requirements: 2.4, 4.1, 4.2, 4.4_

- [ ]* 4.1 Write property test for time range filtering
  - **Property 5: Time range filtering accuracy**
  - **Validates: Requirements 2.4**

- [ ]* 4.2 Write property test for email query parameters
  - **Property 7: Email query parameters**
  - **Validates: Requirements 4.1**

- [ ]* 4.3 Write property test for email data completeness
  - **Property 8: Email data completeness**
  - **Validates: Requirements 4.2**

- [ ]* 4.4 Write property test for Gmail API error handling
  - **Property 9: Gmail API error handling**
  - **Validates: Requirements 4.4**

- [x] 5. Implement Logging Service





  - Create LoggingService class with Python logging module
  - Implement log_input() to record user inputs with timestamp and user_id
  - Implement log_output() to record outputs with timestamp and input reference
  - Implement log_email_retrieval() to record email count and time range
  - Implement log_error() to record exceptions with stack trace and context
  - Configure file handler to write logs to persistent file
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 5.1 Write property test for input logging
  - **Property 13: Input logging**
  - **Validates: Requirements 8.1**

- [ ]* 5.2 Write property test for output logging
  - **Property 14: Output logging**
  - **Validates: Requirements 8.2**

- [ ]* 5.3 Write property test for email retrieval logging
  - **Property 15: Email retrieval logging**
  - **Validates: Requirements 8.3**

- [ ]* 5.4 Write property test for error logging
  - **Property 16: Error logging**
  - **Validates: Requirements 8.4**

- [ ]* 5.5 Write property test for log persistence
  - **Property 17: Log persistence**
  - **Validates: Requirements 8.5**

- [x] 6. Implement NLP Processor





  - Create NLPProcessor class with process_emails() method
  - Implement _extract_keywords() using spaCy or NLTK for keyword extraction
  - Implement _calculate_importance() with heuristic scoring based on keywords (urgent, important, deadline), sender domain, and email length
  - Implement _generate_summary() using extractive summarization techniques
  - Return AnalysisResult with summary, important emails (score > threshold), total count, and method="nlp"
  - _Requirements: 6.2, 6.3, 6.4_

- [x] 7. Implement LLM Processor





  - Create LLMProcessor class with boto3 Bedrock client
  - Implement _format_prompt() to create Claude prompt with email list and instructions for summary and importance identification
  - Implement process_emails() to call AWS Bedrock with model ID "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
  - Implement _parse_response() to extract summary and important emails from Claude's JSON response
  - Return AnalysisResult with summary, important emails, total count, and method="llm"
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 7.1 Write property test for LLM model specification
  - **Property 10: LLM model specification**
  - **Validates: Requirements 5.1**

- [x] 8. Implement Analysis Engine





  - Create AnalysisEngine class with analyze_emails() method
  - Accept emails list and AnalysisMethod enum as parameters
  - Route to LLMProcessor when method is AnalysisMethod.LLM
  - Route to NLPProcessor when method is AnalysisMethod.NLP
  - Return AnalysisResult from selected processor
  - _Requirements: 3.2, 3.3_

- [ ]* 8.1 Write property test for analysis method routing
  - **Property 6: Analysis method routing**
  - **Validates: Requirements 3.2, 3.3**

- [x] 9. Implement FastAPI routes and request validation





  - Create FastAPI app instance with CORS middleware
  - Implement GET /auth/login endpoint to initiate OAuth flow
  - Implement GET /auth/callback endpoint to handle OAuth callback and store credentials
  - Implement GET /auth/status endpoint to check authentication state
  - Implement POST /api/analyze endpoint with request body validation for days_back (positive integer) and method (llm/nlp)
  - Add input validation with Pydantic models
  - Return appropriate error responses for validation failures
  - _Requirements: 2.2, 2.3, 3.4, 9.2, 9.3, 9.4_

- [ ]* 9.1 Write property test for valid time range acceptance
  - **Property 3: Valid time range acceptance**
  - **Validates: Requirements 2.2**

- [ ]* 9.2 Write property test for invalid input rejection
  - **Property 4: Invalid input rejection**
  - **Validates: Requirements 2.3**

- [ ]* 9.3 Write property test for API endpoint availability
  - **Property 18: API endpoint availability**
  - **Validates: Requirements 9.2, 9.3**

- [x] 10. Integrate services in API endpoint handlers





  - In /api/analyze endpoint, retrieve credentials from session using AuthenticationService
  - Instantiate GmailService with credentials
  - Call GmailService.get_unread_emails() with days_back parameter
  - Log email retrieval operation using LoggingService
  - Instantiate AnalysisEngine and call analyze_emails() with emails and selected method
  - Log analysis output using LoggingService
  - Return AnalysisResult as JSON response
  - Wrap all operations in try-except blocks with error logging
  - _Requirements: 4.1, 8.1, 8.2, 8.3_

- [x] 11. Create glassmorphic UI





  - Create HTML template for main dashboard at templates/index.html
  - Add CSS with glassmorphic styling: backdrop-filter blur, semi-transparent backgrounds, subtle borders
  - Create input field for days back with number type validation
  - Create radio buttons for LLM/NLP method selection
  - Create analyze button that triggers POST to /api/analyze
  - Add loading spinner for analysis in progress
  - Create results section with summary display area and important emails list
  - Add error message display area
  - Implement JavaScript to handle form submission, API calls, and result rendering
  - _Requirements: 2.1, 3.1, 7.1, 7.2, 7.3_

- [ ]* 11.1 Write property test for result rendering completeness
  - **Property 12: Result rendering completeness**
  - **Validates: Requirements 7.2, 7.3**

- [x] 12. Implement GET / endpoint to serve UI




  - Create route handler for GET / that returns HTML template
  - Serve static CSS and JavaScript files from /static directory
  - Check authentication status and display login button if not authenticated
  - _Requirements: 9.2_

- [x] 13. Add configuration and environment setup





  - Create config.py to load environment variables using python-dotenv
  - Add validation for required environment variables on startup
  - Configure logging format and file path from environment
  - Set up AWS Bedrock client configuration with region and credentials
  - Configure Google OAuth client with client ID and secret
  - _Requirements: 1.1, 5.1_

- [x] 14. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Create documentation and deployment files





  - Write README.md with setup instructions, environment variable documentation, and usage guide
  - Create .env.example with all required environment variables
  - Document Gmail API setup steps and required OAuth scopes
  - Document AWS Bedrock access requirements and IAM permissions
  - Add inline code comments for complex logic
  - Create one documnt for BLOG post also
  - _Requirements: All_

- [x] 16. Final checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
