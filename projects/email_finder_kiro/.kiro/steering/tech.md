# Technology Stack

## Core Framework
- **FastAPI**: Web framework for API and UI serving
- **Python 3.9+**: Primary language
- **Uvicorn**: ASGI server for running FastAPI

## Key Libraries

### Authentication & APIs
- `google-auth`, `google-auth-oauthlib`: Gmail OAuth2 authentication
- `google-api-python-client`: Gmail API integration
- `boto3`: AWS Bedrock client for LLM access

### AI & NLP
- **AWS Bedrock**: Claude 3.7 Sonnet model (`us.anthropic.claude-3-7-sonnet-20250219-v1:0`)
- `nltk`: Traditional NLP processing (tokenization, stopwords, frequency analysis)

### Data & Configuration
- `pydantic`: Data validation and models
- `python-dotenv`: Environment variable management
- `jinja2`: HTML templating

### Testing
- `pytest`: Test framework
- `hypothesis`: Property-based testing
- `unittest.mock`: Mocking for unit tests

## Common Commands

### Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

### Running
```bash
# Development server with auto-reload
uvicorn api.main:app --reload

# Alternative
python -m uvicorn api.main:app --reload
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_gmail_service.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## AWS Configuration

### Required Credentials
- AWS Access Key ID and Secret Access Key with Bedrock permissions
- Session token support for temporary credentials (AWS_SESSION_TOKEN)
- Region: us-east-1 (default)

### IAM Permissions
Minimum required: `bedrock:InvokeModel` on Claude models

## Environment Variables

### Required
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth credentials
- `GOOGLE_REDIRECT_URI`: OAuth callback (default: `http://localhost:8000/auth/callback`)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_SESSION_TOKEN`: Required for temporary AWS credentials
- `SESSION_SECRET_KEY`: Session encryption key

### Optional
- `AWS_REGION`: AWS region (default: us-east-1)
- `LOG_FILE_PATH`: Log file location (default: logs/app.log)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEBUG`: Debug mode (default: False)
- `HOST`, `PORT`: Server configuration
