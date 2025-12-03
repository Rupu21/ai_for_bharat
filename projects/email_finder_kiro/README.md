# Email Insights Dashboard

A FastAPI-based web application that provides intelligent analysis of unread Gmail messages using LLM (AWS Bedrock Claude) or traditional NLP methods.

## Features

- **Gmail OAuth2 Authentication**: Secure access to your Gmail account
- **Flexible Time Range**: Analyze unread emails from the last N days
- **Dual Analysis Modes**: 
  - LLM (AWS Bedrock Claude 3.7 Sonnet) for deep semantic understanding
  - Traditional NLP (spaCy/NLTK) for fast, local processing
- **Real-Time Progress Updates**: Live feedback during analysis with Server-Sent Events
- **Modern Glassmorphic UI**: Beautiful, intuitive interface with transparency and blur effects
- **Comprehensive Logging**: All operations logged for audit and troubleshooting
- **Important Email Detection**: Automatically identifies emails requiring attention
- **Smart Summarization**: Get concise summaries of your unread emails
- **Production Ready**: Docker support, health checks, optimized performance
- **Fast & Efficient**: Optimized for low latency and reduced AWS costs

## Table of Contents

- [Prerequisites](#prerequisites)
- [Gmail API Setup](#gmail-api-setup)
- [AWS Bedrock Setup](#aws-bedrock-setup)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.9 or higher**
- **Google Cloud Project** with Gmail API enabled
- **AWS Account** with Bedrock access and Claude 3.7 Sonnet model enabled
- **pip** package manager
- **Internet connection** for API access

## Gmail API Setup

Follow these steps to set up Gmail API access:

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Email Insights Dashboard")
4. Click "Create"

### 2. Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: Select "External" (or "Internal" if using Google Workspace)
   - App name: "Email Insights Dashboard"
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `https://www.googleapis.com/auth/gmail.readonly`
   - Test users: Add your Gmail address
   - Click "Save and Continue"
4. Back in Credentials, click "Create Credentials" → "OAuth client ID"
5. Application type: "Web application"
6. Name: "Email Insights Dashboard"
7. Authorized redirect URIs: Add `http://localhost:8000/auth/callback`
8. Click "Create"
9. **Copy the Client ID and Client Secret** - you'll need these for `.env`

### 4. Required OAuth Scopes

The application requires the following Gmail API scope:
- `https://www.googleapis.com/auth/gmail.readonly` - Read-only access to Gmail messages

This scope allows the application to:
- Read email metadata (subject, sender, timestamp)
- Read email content (body, snippets)
- Query unread emails
- **Does NOT allow**: Sending emails, deleting emails, or modifying email content

## AWS Bedrock Setup

Follow these steps to set up AWS Bedrock access:

### 1. Create an AWS Account

If you don't have an AWS account, create one at [aws.amazon.com](https://aws.amazon.com/)

### 2. Enable Bedrock Model Access

1. Sign in to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Bedrock** service
3. In the left sidebar, click "Model access"
4. Click "Manage model access" or "Enable specific models"
5. Find **Anthropic Claude 3.7 Sonnet** in the list
6. Check the box next to it
7. Click "Request model access" or "Save changes"
8. Wait for approval (usually instant for Claude models)

**Required Model:**
- Model ID: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- Provider: Anthropic
- Region: us-east-1 (or your preferred region)

### 3. Create IAM User with Bedrock Permissions

1. Go to **IAM** service in AWS Console
2. Click "Users" → "Add users"
3. Username: `email-insights-bedrock-user`
4. Select "Access key - Programmatic access"
5. Click "Next: Permissions"
6. Click "Attach existing policies directly"
7. Search for and select: `AmazonBedrockFullAccess`
   - Or create a custom policy with minimal permissions (see below)
8. Click "Next: Tags" → "Next: Review" → "Create user"
9. **Copy the Access Key ID and Secret Access Key** - you'll need these for `.env`
10. **Important**: Save these credentials securely - the secret key won't be shown again

### 4. Minimal IAM Policy (Recommended)

For better security, use this minimal policy instead of `AmazonBedrockFullAccess`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
    }
  ]
}
```

To create this policy:
1. Go to IAM → Policies → Create policy
2. Click "JSON" tab and paste the policy above
3. Name it `BedrockClaudeInvokeOnly`
4. Attach this policy to your IAM user instead of `AmazonBedrockFullAccess`

### 5. Verify Bedrock Access

Test your setup with AWS CLI (optional):
```bash
aws bedrock list-foundation-models --region us-east-1
```

You should see Claude models in the output.

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd email-insights-dashboard
```

### 2. Create a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment Configuration

Copy the example environment file and fill in your credentials:

**On macOS/Linux:**
```bash
cp .env.example .env
```

**On Windows:**
```bash
copy .env.example .env
```

Now edit `.env` with your actual credentials (see [Configuration](#configuration) section)

### Configuration

The application uses a centralized configuration system that loads settings from environment variables. All configuration is managed through the `config.py` module.

#### Required Environment Variables

Edit `.env` file with your credentials:

**Google OAuth Configuration:**
- `GOOGLE_CLIENT_ID`: OAuth 2.0 client ID from [Google Cloud Console](https://console.cloud.google.com/)
- `GOOGLE_CLIENT_SECRET`: OAuth 2.0 client secret
- `GOOGLE_REDIRECT_URI`: OAuth callback URL (default: `http://localhost:8000/auth/callback`)

**AWS Bedrock Configuration:**
- `AWS_ACCESS_KEY_ID`: AWS access key with Bedrock permissions
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key
- `AWS_REGION`: AWS region (default: `us-east-1`)

**Application Configuration:**
- `SESSION_SECRET_KEY`: Random secret key for session management
  - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

#### Optional Environment Variables

**Logging Configuration:**
- `LOG_FILE_PATH`: Path to log file (default: `logs/app.log`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FORMAT`: Log message format
- `LOG_DATE_FORMAT`: Log timestamp format

**Application Settings:**
- `DEBUG`: Enable debug mode (default: `False`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)

The configuration module validates all required variables on startup and provides helpful error messages if any are missing.

### Running the Application

Start the FastAPI development server:

```bash
uvicorn api.main:app --reload
```

Or use the Python module directly:

```bash
python -m uvicorn api.main:app --reload
```

The application will be available at:
- **Main UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Usage

### First Time Setup

1. **Start the application** (see [Running the Application](#running-the-application))
2. **Open your browser** and navigate to http://localhost:8000
3. **Authenticate with Gmail**:
   - Click the "Login with Gmail" button
   - You'll be redirected to Google's OAuth consent screen
   - Select your Gmail account
   - Review the permissions (read-only access to Gmail)
   - Click "Allow"
   - You'll be redirected back to the dashboard

### Analyzing Your Emails

1. **Set Time Range**: Select from dropdown (Last 24 hours, 3 days, week, 2 weeks, or month)
   - The system will analyze unread emails within this range
   - Optimized to process up to 100 emails for best performance

2. **Choose Analysis Method**:
   - **LLM (Recommended)**: Uses AWS Bedrock Claude 3.7 Sonnet for deep semantic analysis
     - Pros: More accurate, better context understanding, identifies subtle importance cues
     - Response time: 5-15 seconds
   - **NLP (Fast)**: Uses traditional NLP with spaCy and NLTK
     - Pros: Fast (2-5 seconds), runs locally, no API costs
     - Cons: Less sophisticated, rule-based importance detection

3. **Click "Analyze"**: Watch real-time progress updates! 🎉
   - ⏳ Connecting to Gmail...
   - ✓ Connected to Gmail
   - ⏳ Retrieving unread emails...
   - ✓ Retrieved X unread emails
   - ⏳ Analyzing with LLM/NLP...
   - ✓ Analysis complete!

### Understanding Results

**Stats Dashboard:**
- Total unread emails count
- Number of important emails identified
- Analysis method used

**Summary Section:**
- Concise overview of your unread emails
- Common themes and topics
- Quick snapshot of your inbox

**Important Emails Section:**
- Emails requiring your attention
- Importance score (0.0-1.0)
- Reason why each email is important
- Sender, subject, snippet, and timestamp
- Hover effects for better readability

### Tips for Best Results

- **Use LLM for important decisions**: When you need accurate prioritization
- **Use NLP for quick checks**: When you just want a fast overview
- **Start with "Last week"**: Good balance of coverage and speed
- **Watch the progress**: Real-time updates keep you informed
- **Check logs**: If something goes wrong, check `logs/app.log` for details

## Project Structure

```
.
├── api/              # FastAPI routes
├── models/           # Data models
├── services/         # Business logic services
├── static/           # CSS, JavaScript
├── templates/        # HTML templates
├── tests/            # Unit and property tests
├── logs/             # Application logs
├── main.py           # Application entry point
└── config.py         # Configuration management
```

## Testing

The project includes comprehensive unit tests and property-based tests.

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

**Unit tests only:**
```bash
pytest tests/unit/
```

**Property-based tests only:**
```bash
pytest tests/property/
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

View coverage report by opening `htmlcov/index.html` in your browser.

### Run Specific Test File

```bash
pytest tests/unit/test_gmail_service.py
```

### Verbose Output

```bash
pytest -v
```

### Property-Based Testing

The project uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing. These tests run 100+ iterations with randomly generated inputs to verify correctness properties.

## Troubleshooting

### Common Issues

#### "Invalid credentials" error

**Problem**: OAuth authentication fails

**Solutions**:
- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
- Check that redirect URI matches exactly: `http://localhost:8000/auth/callback`
- Ensure Gmail API is enabled in Google Cloud Console
- Try deleting browser cookies and re-authenticating

#### "Model not found" or Bedrock access denied

**Problem**: Cannot access Claude model

**Solutions**:
- Verify you've enabled Claude 3.7 Sonnet in Bedrock console
- Check AWS credentials in `.env` are correct
- Ensure IAM user has `bedrock:InvokeModel` permission
- Verify the region is correct (default: us-east-1)
- Check model ID: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`

#### "No unread emails found"

**Problem**: Analysis returns empty results

**Solutions**:
- Verify you have unread emails in the specified time range
- Check that OAuth scope includes `gmail.readonly`
- Try increasing the days back parameter
- Check logs for Gmail API errors

#### Port already in use

**Problem**: `Address already in use`

**Solutions**:
- Change port in `.env`: `PORT=8001`
- Or kill the process using port 8000:
  - Linux/Mac: `lsof -ti:8000 | xargs kill -9`
  - Windows: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`

#### Session expired

**Problem**: "Please log in again" message

**Solutions**:
- This is normal after ~1 hour of inactivity
- Simply click "Login with Gmail" again
- For longer sessions, implement token refresh (see `auth_service.py`)

### Logging

Check application logs for detailed error information:

```bash
tail -f logs/app.log
```

Or view the entire log:

```bash
cat logs/app.log
```

Logs include:
- All user inputs and outputs
- Email retrieval operations
- Analysis method selections
- Error stack traces
- API call details

### Getting Help

If you encounter issues not covered here:

1. Check the logs: `logs/app.log`
2. Review the error message carefully
3. Verify all environment variables are set correctly
4. Ensure all prerequisites are installed
5. Try running tests to identify the issue: `pytest -v`

## Security Notes

- **Never commit `.env` file** to version control
- **Rotate credentials regularly**, especially if exposed
- **Use minimal IAM permissions** for AWS (see AWS Bedrock Setup)
- **OAuth tokens are session-only** and not persisted to disk
- **Logs may contain email metadata** - secure log files appropriately
- **Use HTTPS in production** to protect credentials in transit

## Performance Considerations

**Optimized for Speed:**
- **LLM Analysis**: 5-15 seconds (up to 50 emails)
- **NLP Analysis**: 2-5 seconds (up to 100 emails)
- **Real-time progress**: Live updates during analysis
- **Reduced costs**: 50% lower AWS Bedrock usage

**Resource Usage:**
- **Memory**: ~100-200MB
- **CPU**: Low usage (mostly I/O bound)
- **Network**: Optimized with GZip compression

**Limits:**
- Gmail API: Max 100 emails fetched
- LLM Processing: Max 50 emails analyzed
- Rate limiting: 250 quota units/user/second (Gmail API)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- LLM powered by [AWS Bedrock](https://aws.amazon.com/bedrock/) and [Anthropic Claude](https://www.anthropic.com/)
- NLP powered by [spaCy](https://spacy.io/) and [NLTK](https://www.nltk.org/)
- Gmail integration via [Google APIs](https://developers.google.com/gmail/api)
- Property-based testing with [Hypothesis](https://hypothesis.readthedocs.io/)
