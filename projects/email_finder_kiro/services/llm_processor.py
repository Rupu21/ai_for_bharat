"""
LLM Processor for email analysis using AWS Bedrock Claude.

This module provides LLM-based analysis of emails using AWS Bedrock's
Claude 3.7 Sonnet model for intelligent summarization and importance identification.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config as BotoConfig

from models.data_models import Email, AnalysisResult, ImportantEmail
from config import get_config


class LLMProcessor:
    """
    Processes emails using AWS Bedrock Claude LLM.
    
    This processor:
    - Formats emails into prompts for Claude
    - Calls AWS Bedrock with Claude 3.7 Sonnet model
    - Parses LLM responses into structured results
    """
    
    def __init__(self, config=None, bedrock_client=None):
        """
        Initialize LLM Processor with AWS Bedrock client.
        
        Args:
            config: Optional Config instance. If None, uses global config.
            bedrock_client: Optional boto3 Bedrock client. If not provided,
                          will be created from config.
        """
        self.config = config or get_config()
        
        # Get model configuration from config
        self.model_id = self.config.bedrock_model_id
        self.max_tokens = self.config.bedrock_max_tokens
        
        # Initialize Bedrock client with optimized settings
        if bedrock_client is None:
            # Configure boto3 for better performance
            boto_config = BotoConfig(
                connect_timeout=10,
                read_timeout=60,
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
            
            client_kwargs = {
                'service_name': 'bedrock-runtime',
                'aws_access_key_id': self.config.aws_access_key_id,
                'aws_secret_access_key': self.config.aws_secret_access_key,
                'region_name': self.config.aws_region,
                'config': boto_config
            }
            
            # Add session token if provided
            if hasattr(self.config, 'aws_session_token') and self.config.aws_session_token:
                client_kwargs['aws_session_token'] = self.config.aws_session_token
            
            self.bedrock_client = boto3.client(**client_kwargs)
        else:
            self.bedrock_client = bedrock_client
    
    def process_emails(self, emails: List[Email]) -> AnalysisResult:
        """
        Analyzes emails using Claude LLM via AWS Bedrock.
        
        Args:
            emails: List of Email objects to analyze
            
        Returns:
            AnalysisResult: Analysis results with summary and important emails
            
        Raises:
            ClientError: If AWS Bedrock API call fails
        """
        if not emails:
            return AnalysisResult(
                summary="No unread emails found.",
                important_emails=[],
                total_unread=0,
                analysis_method="llm",
                timestamp=datetime.now()
            )
        
        # Format prompt for Claude
        prompt = self._format_prompt(emails)
        
        # Call AWS Bedrock
        try:
            response = self._call_bedrock(prompt)
            
            # Parse response into structured result
            analysis_result = self._parse_response(response, emails)
            
            return analysis_result
            
        except ClientError as e:
            # Log error and raise for handling at higher level
            error_message = f"AWS Bedrock API error: {str(e)}"
            raise RuntimeError(error_message) from e
    
    def _format_prompt(self, emails: List[Email]) -> str:
        """
        Creates a prompt for Claude with email list and analysis instructions.
        
        Args:
            emails: List of Email objects
            
        Returns:
            str: Formatted prompt for Claude
        """
        # Limit to most recent 50 emails for performance
        emails_to_process = emails[:50] if len(emails) > 50 else emails
        
        # Build email list for prompt with optimized length
        email_list = []
        for idx, email in enumerate(emails_to_process, 1):
            # Truncate body to 500 chars for faster processing
            body_preview = email.body[:500] if email.body else email.snippet[:200] if email.snippet else ''
            email_text = f"""
Email {idx}:
Subject: {email.subject}
From: {email.sender} <{email.sender_email}>
Date: {email.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Body: {body_preview}{'...' if len(email.body) > 500 else ''}
"""
            email_list.append(email_text.strip())
        
        emails_text = "\n\n".join(email_list)
        
        # Add note if emails were limited
        limit_note = f"\n\nNote: Showing {len(emails_to_process)} most recent emails out of {len(emails)} total." if len(emails) > 50 else ""
        
        # Create comprehensive prompt
        prompt = f"""You are an email analysis assistant. Analyze the following {len(emails_to_process)} unread emails and provide:

1. A concise summary of all emails (2-3 sentences)
2. Identify which emails are important and need attention (max 10)
3. For each important email, provide an importance score (0.0-1.0) and brief reason

{emails_text}{limit_note}

Respond in JSON format:
{{
    "summary": "Your summary here",
    "important_emails": [
        {{
            "email_index": 1,
            "importance_score": 0.85,
            "reason": "Brief explanation"
        }}
    ]
}}

Consider emails important if they:
- Contain urgent keywords (deadline, urgent, important, ASAP)
- Require action or response
- Are from work/professional contacts
- Contain time-sensitive information

Respond only with valid JSON."""
        
        return prompt
    
    def _call_bedrock(self, prompt: str) -> Dict[str, Any]:
        """
        Calls AWS Bedrock with the formatted prompt.
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            Dict: Response from Bedrock API
            
        Raises:
            ClientError: If API call fails
        """
        # Prepare request body for Claude with optimized settings
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": min(self.max_tokens, 2048),  # Reduce for faster response
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5  # Lower temperature for more consistent, faster responses
        }
        
        # Call Bedrock with timeout handling
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        return response_body
    
    def _parse_response(self, response: Dict[str, Any], emails: List[Email]) -> AnalysisResult:
        """
        Extracts summary and important emails from Claude's response.
        
        Args:
            response: Response dictionary from Bedrock
            emails: Original list of Email objects
            
        Returns:
            AnalysisResult: Structured analysis result
        """
        # Extract content from Claude response
        content = response.get('content', [])
        
        if not content:
            # Fallback if no content
            return AnalysisResult(
                summary="Unable to generate summary.",
                important_emails=[],
                total_unread=len(emails),
                analysis_method="llm",
                timestamp=datetime.now()
            )
        
        # Get text content
        text_content = ""
        for block in content:
            if block.get('type') == 'text':
                text_content = block.get('text', '')
                break
        
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            # Claude might wrap it in markdown code blocks
            json_text = text_content.strip()
            
            # Remove markdown code blocks if present
            if json_text.startswith('```'):
                lines = json_text.split('\n')
                json_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_text
                json_text = json_text.replace('```json', '').replace('```', '').strip()
            
            parsed_data = json.loads(json_text)
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return AnalysisResult(
                summary=text_content[:500] if text_content else "Unable to parse analysis results.",
                important_emails=[],
                total_unread=len(emails),
                analysis_method="llm",
                timestamp=datetime.now()
            )
        
        # Extract summary
        summary = parsed_data.get('summary', 'No summary provided.')
        
        # Extract important emails
        important_emails = []
        important_email_data = parsed_data.get('important_emails', [])
        
        for item in important_email_data:
            email_index = item.get('email_index', 0) - 1  # Convert to 0-based index
            
            # Validate index
            if 0 <= email_index < len(emails):
                email = emails[email_index]
                importance_score = float(item.get('importance_score', 0.5))
                reason = item.get('reason', 'Identified as important by LLM')
                
                # Ensure score is in valid range
                importance_score = max(0.0, min(1.0, importance_score))
                
                important_emails.append(
                    ImportantEmail(
                        email=email,
                        importance_score=importance_score,
                        reason=reason
                    )
                )
        
        # Sort by importance score (highest first)
        important_emails.sort(key=lambda x: x.importance_score, reverse=True)
        
        return AnalysisResult(
            summary=summary,
            important_emails=important_emails,
            total_unread=len(emails),
            analysis_method="llm",
            timestamp=datetime.now()
        )
