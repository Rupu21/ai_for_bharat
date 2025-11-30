# Web Content Summarizer

A FastAPI-based web application that extracts and summarizes content from any publicly accessible website URL using AWS Bedrock with Claude 3.7 Sonnet.

## Features

- 🌐 Fetch content from any public URL
- 🤖 AI-powered summarization using Claude 3.7 Sonnet
- ✨ Extract key highlights automatically
- 🎨 Modern glassmorphic UI design
- ⚡ Fast and responsive

## Prerequisites

- Python 3.9 or higher
- AWS Account with Bedrock access
- AWS CLI configured or AWS credentials

## Setup

### 1. Clone and Navigate to Project

```bash
cd web-content-summarizer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure AWS Credentials

You have two options:

#### Option A: Using Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

Then load the environment variables before running the app.

#### Option B: Using AWS CLI Configuration

If you have AWS CLI installed and configured, boto3 will automatically use those credentials:

```bash
aws configure
```

Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (e.g., json)

### 6. Verify AWS Bedrock Access

Make sure your AWS account has access to the Claude 3.7 Sonnet model:
- Model ID: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- You may need to request access in the AWS Bedrock console

## Running the Application

### Start the Development Server

```bash
uvicorn main:app --reload
```

The application will be available at: `http://localhost:8000`

### Run Tests

```bash
pytest tests/ -v
```

## Usage

1. Open your browser and navigate to `http://localhost:8000`
2. Enter a website URL in the input field
3. Click "Summarize" or press Enter
4. View the AI-generated summary and key highlights

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── validators.py      # URL validation
│   ├── fetcher.py         # Content fetching
│   ├── extractor.py       # Text extraction
│   └── summarizer.py      # AI summarization
├── static/
│   ├── index.html         # Frontend UI
│   ├── style.css          # Glassmorphic styling
│   └── script.js          # Frontend logic
├── tests/
│   └── test_*.py          # Test files
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` |
| `BEDROCK_MODEL_ID` | Bedrock model ID | `us.anthropic.claude-3-7-sonnet-20250219-v1:0` |
| `BEDROCK_MAX_TOKENS` | Max tokens for response | `1000` |

## Troubleshooting

### AWS Credentials Error

If you see "Service configuration error", check:
- AWS credentials are correctly set
- Your AWS account has Bedrock access
- The Claude 3.7 Sonnet model is available in your region

### Module Not Found Error

Make sure you've activated the virtual environment and installed dependencies:
```bash
pip install -r requirements.txt
```

## License

MIT License
