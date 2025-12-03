# Project Structure

## Directory Organization

```
.
├── api/                    # FastAPI application and routes
│   ├── main.py            # Main FastAPI app, endpoints, middleware
│   └── __init__.py
├── models/                 # Data models and schemas
│   ├── data_models.py     # Email, AnalysisResult, ImportantEmail dataclasses
│   └── __init__.py
├── services/               # Business logic layer
│   ├── analysis_engine.py # Routes analysis to LLM or NLP processors
│   ├── auth_service.py    # OAuth2 flow and credential management
│   ├── gmail_service.py   # Gmail API integration and email parsing
│   ├── llm_processor.py   # AWS Bedrock Claude integration
│   ├── nlp_processor.py   # Traditional NLP with spaCy/NLTK
│   ├── logging_service.py # Centralized logging
│   └── __init__.py
├── templates/              # Jinja2 HTML templates
│   └── index.html         # Main dashboard UI
├── static/                 # CSS, JavaScript, images
├── tests/                  # Test suite
│   ├── unit/              # Unit tests for each service
│   ├── property/          # Property-based tests with Hypothesis
│   └── __init__.py
├── logs/                   # Application logs
│   └── app.log
├── config.py              # Centralized configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
└── .env.example          # Environment template
```

## Architecture Patterns

### Layered Architecture
- **API Layer** (`api/`): HTTP endpoints, request validation, response formatting
- **Service Layer** (`services/`): Business logic, external API integration
- **Model Layer** (`models/`): Data structures and validation
- **Configuration** (`config.py`): Centralized config with validation

### Service Pattern
Each service is a self-contained class with single responsibility:
- `AuthenticationService`: OAuth flow management
- `GmailService`: Email retrieval and parsing
- `AnalysisEngine`: Routes to appropriate processor
- `LLMProcessor`: AWS Bedrock integration
- `NLPProcessor`: Traditional NLP analysis
- `LoggingService`: Structured logging

### Dependency Injection
Services accept dependencies via constructor:
```python
def __init__(self, config=None, llm_processor=None):
    self.config = config or get_config()
    self.llm_processor = llm_processor or LLMProcessor(config)
```

### Configuration Management
- Single `Config` class loads and validates all environment variables
- Global `get_config()` function provides singleton instance
- Services receive config via constructor for testability
- Lazy initialization pattern for optional dependencies

## Code Conventions

### Naming
- Classes: PascalCase (`GmailService`, `AnalysisEngine`)
- Functions/methods: snake_case (`get_unread_emails`, `parse_email`)
- Constants: UPPER_SNAKE_CASE (`AWS_REGION`, `LOG_LEVEL`)
- Private methods: prefix with underscore (`_parse_sender`, `_decode_body_data`)

### Docstrings
All modules, classes, and public methods have docstrings:
```python
"""
Brief description.

Longer explanation if needed.

Args:
    param: Description
    
Returns:
    Type: Description
    
Raises:
    ExceptionType: When this happens
"""
```

### Error Handling
- Validate inputs early, raise `ValueError` for invalid parameters
- Catch specific exceptions, re-raise as `RuntimeError` with context
- Log errors before raising
- Use descriptive error messages

### Testing
- Unit tests in `tests/unit/` mirror source structure
- Use `unittest.mock` for external dependencies
- Property-based tests in `tests/property/` for invariants
- Test class names: `Test<ClassName><Aspect>`
- Test method names: `test_<method>_<scenario>`

## Data Flow

1. **Request** → `api/main.py` endpoint
2. **Validation** → Pydantic models validate input
3. **Authentication** → `AuthenticationService` checks session
4. **Email Retrieval** → `GmailService` fetches from Gmail API
5. **Analysis** → `AnalysisEngine` routes to processor
6. **Processing** → `LLMProcessor` or `NLPProcessor` analyzes
7. **Logging** → `LoggingService` records operation
8. **Response** → Formatted JSON returned to client

## Key Files

- `config.py`: Single source of truth for all configuration
- `api/main.py`: All HTTP endpoints and FastAPI setup
- `models/data_models.py`: Core data structures used throughout
- `services/analysis_engine.py`: Central routing for analysis methods
- `requirements.txt`: All Python dependencies with pinned versions
