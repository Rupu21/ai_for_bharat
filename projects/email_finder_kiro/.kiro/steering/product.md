# Product Overview

Email Insights Dashboard is a FastAPI-based web application that analyzes unread Gmail messages using AI and NLP techniques.

## Core Features

- **Gmail OAuth2 Authentication**: Secure read-only access to Gmail accounts
- **Dual Analysis Modes**: 
  - LLM mode using AWS Bedrock Claude 3.7 Sonnet for semantic understanding
  - NLP mode using spaCy/NLTK for fast local processing
- **Smart Email Prioritization**: Automatically identifies important emails requiring attention
- **Time-Range Filtering**: Analyze unread emails from the last 1-365 days
- **Comprehensive Logging**: All operations logged for audit and troubleshooting

## User Flow

1. User authenticates with Gmail via OAuth2
2. User selects time range (days back) and analysis method (LLM or NLP)
3. System retrieves unread emails from Gmail API
4. System analyzes emails and generates summary with important email highlights
5. Results displayed in glassmorphic UI with importance scores and reasons

## Key Value Proposition

Helps users quickly understand their unread inbox by providing intelligent summaries and highlighting emails that need immediate attention, saving time and reducing email overload.
