# Email Insights Dashboard API

FastAPI application for analyzing unread Gmail messages.

## Running the Application

To start the development server:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `GET /auth/login` - Initiates OAuth2 flow with Google
- `GET /auth/callback` - Handles OAuth callback
- `GET /auth/status` - Checks authentication status

### Analysis
- `POST /api/analyze` - Analyzes unread emails
  - Request body: `{"days_back": int, "method": "llm" | "nlp"}`
  - Requires authentication

### Health
- `GET /health` - Health check endpoint

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Required environment variables (see `.env.example`):
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `LOG_FILE_PATH`
