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
    
    def _select_emails_smartly(self, emails: List[Email], max_count: int = 50) -> List[Email]:
        """
        Intelligently selects emails to analyze when count exceeds limit.
        
        Strategy:
        1. Always include most recent 30 emails (likely most relevant)
        2. Scan remaining emails for importance indicators
        3. Fill remaining slots with potentially important emails
        
        Args:
            emails: Full list of emails
            max_count: Maximum number of emails to select
            
        Returns:
            List[Email]: Selected emails for analysis
        """
        if len(emails) <= max_count:
            return emails
        
        # Keywords that indicate importance
        importance_keywords = {
            'urgent', 'important', 'deadline', 'asap', 'critical', 'priority',
            'action required', 'time sensitive', 'immediate', 'emergency',
            'attention', 'required', 'respond', 'reply', 'confirm', 'approval',
            'meeting', 'interview', 'offer', 'contract', 'invoice', 'payment'
        }
        
        # 1. Always take most recent 30 emails
        recent_count = min(30, max_count)
        selected_emails = emails[:recent_count]
        remaining_slots = max_count - recent_count
        
        if remaining_slots <= 0:
            return selected_emails
        
        # 2. Score remaining emails for importance
        remaining_emails = emails[recent_count:]
        scored_emails = []
        
        for email in remaining_emails:
            score = 0
            text = f"{email.subject} {email.body}".lower()
            
            # Check for importance keywords
            for keyword in importance_keywords:
                if keyword in text:
                    score += 1
            
            # Boost score for work domains
            if not any(domain in email.sender_email.lower() 
                      for domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']):
                score += 2
            
            # Boost for longer emails (more substantial)
            if len(email.body) > 1000:
                score += 1
            
            scored_emails.append((score, email))
        
        # 3. Sort by score and take top emails
        scored_emails.sort(key=lambda x: x[0], reverse=True)
        selected_emails.extend([email for score, email in scored_emails[:remaining_slots]])
        
        return selected_emails
    
    def process_emails(self, emails: List[Email]) -> AnalysisResult:
        """
        Analyzes emails using Claude LLM via AWS Bedrock.
        Uses smart selection to prioritize important emails when count is high.
        
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
        
        # Select emails smartly if too many
        emails_to_analyze = self._select_emails_smartly(emails, max_count=50)
        
        # Format prompt for Claude
        prompt = self._format_prompt(emails_to_analyze)
        
        # Call AWS Bedrock
        try:
            response = self._call_bedrock(prompt)
            
            # Parse response into structured result
            # Pass original emails list for proper indexing
            analysis_result = self._parse_response(response, emails_to_analyze)
            
            # Update total count to reflect all emails
            analysis_result.total_unread = len(emails)
            
            # Add note to summary if emails were filtered
            if len(emails) > len(emails_to_analyze):
                analysis_result.summary += f" (Analyzed {len(emails_to_analyze)} prioritized emails out of {len(emails)} total.)"
            
            return analysis_result
            
        except ClientError as e:
            # Log error and raise for handling at higher level
            error_message = f"AWS Bedrock API error: {str(e)}"
            raise RuntimeError(error_message) from e
    
    def _extract_email_preview(self, email: Email) -> str:
        """
        Extracts the most relevant preview from an email.
        Prioritizes: Subject + First 2-3 lines of body.
        
        Args:
            email: Email object
            
        Returns:
            str: Concise preview of email content
        """
        # Start with snippet if available (Gmail's smart preview)
        if email.snippet and len(email.snippet) > 50:
            preview = email.snippet[:300]
        elif email.body:
            # Extract first few lines of body
            lines = email.body.split('\n')
            # Filter out empty lines
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            # Take first 2-3 meaningful lines
            preview_lines = non_empty_lines[:3]
            preview = ' '.join(preview_lines)
            
            # Limit to ~300 chars
            if len(preview) > 300:
                preview = preview[:300]
        else:
            preview = "(No content available)"
        
        # Clean up common email artifacts
        preview = preview.replace('\r', ' ').replace('\t', ' ')
        # Remove multiple spaces
        preview = ' '.join(preview.split())
        
        return preview
    
    def _format_prompt(self, emails: List[Email]) -> str:
        """
        Creates a prompt for Claude with email list and analysis instructions.
        Uses smart batching to prioritize recent and potentially important emails.
        
        Args:
            emails: List of Email objects
            
        Returns:
            str: Formatted prompt for Claude
        """
        # Smart email selection strategy
        if len(emails) <= 50:
            # Process all emails if within limit
            emails_to_process = emails
        else:
            # Use hybrid approach: recent + keyword-filtered
            emails_to_process = self._select_emails_smartly(emails, max_count=50)
        
        # Build email list for prompt with optimized content
        email_list = []
        for idx, email in enumerate(emails_to_process, 1):
            # Extract first 2-3 lines of body (most important info)
            body_preview = self._extract_email_preview(email)
            
            email_text = f"""
Email {idx}:
Subject: {email.subject}
From: {email.sender} <{email.sender_email}>
Date: {email.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Preview: {body_preview}
"""
            email_list.append(email_text.strip())
        
        emails_text = "\n\n".join(email_list)
        
        # Add note if emails were limited
        limit_note = ""
        if len(emails) > 50:
            limit_note = f"\n\nNote: Analyzed {len(emails_to_process)} prioritized emails out of {len(emails)} total (most recent + potentially important)."
        
        # Create comprehensive prompt
        prompt = f"""You are an email analysis assistant. Analyze the following {len(emails_to_process)} unread emails.

Each email shows: Subject, Sender, Date, and Preview (first 2-3 lines of content).

{emails_text}{limit_note}

Provide:
1. A concise summary of all emails (2-3 sentences)
2. Identify important emails (max 10) with importance score (0.0-1.0) and reason

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
- Contain urgent keywords (deadline, urgent, important, ASAP, critical)
- Require action or response (reply, confirm, approve, review)
- Are from work/professional contacts
- Contain time-sensitive information (meeting, interview, deadline)
- Have significant business implications (contract, invoice, offer)

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
