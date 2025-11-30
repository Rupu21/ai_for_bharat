"""Content summarization module using AWS Bedrock with Claude 3.7 Sonnet."""

import json
import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError


# AWS Bedrock configuration
BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID", 
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
)
BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "1000"))
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Content length limits (Claude has token limits)
MAX_CONTENT_LENGTH = 50000  # characters


def _get_bedrock_client():
    """
    Creates and returns a boto3 Bedrock Runtime client.
    
    Returns:
        boto3 client for Bedrock Runtime
    """
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION
    )


def _truncate_content(text: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """
    Truncates content to fit within token limits.
    
    Args:
        text: The text to truncate
        max_length: Maximum character length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Truncate and add indicator
    return text[:max_length] + "... [content truncated]"


def generate_summary(text: str) -> tuple[str | None, str | None]:
    """
    Generates a summary from text content using AWS Bedrock with Claude 3.7 Sonnet.
    
    Args:
        text: The text content to summarize
        
    Returns:
        A tuple of (summary_text, error_message) where:
        - summary_text: The generated summary if successful, None if error
        - error_message: None if successful, error description if failed
    """
    # Handle empty or very short content
    if not text or not text.strip():
        return None, "No content available to summarize"
    
    # If content is very short, return it as-is
    if len(text.strip()) < 100:
        return text.strip(), None
    
    # Truncate if content is too long
    truncated_text = _truncate_content(text)
    
    try:
        # Get Bedrock client
        client = _get_bedrock_client()
        
        # Prepare the prompt for Claude
        prompt = f"""Please provide a concise summary of the following web content. 
Focus on the main ideas and key points. Keep the summary clear and informative.

Content:
{truncated_text}

Summary:"""
        
        # Prepare the request body for Claude 3.7 Sonnet
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": BEDROCK_MAX_TOKENS,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # Invoke the model
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the summary from Claude's response
        if 'content' in response_body and len(response_body['content']) > 0:
            summary = response_body['content'][0]['text'].strip()
            return summary, None
        else:
            return None, "Failed to generate summary. Please try again."
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', '')
        
        if error_code == 'AccessDeniedException':
            return None, "AWS credentials are invalid or expired. Please check your AWS configuration."
        elif error_code == 'ThrottlingException':
            return None, "Service is busy due to rate limiting. Please try again in a moment."
        elif error_code == 'ValidationException':
            return None, "Invalid request to AI service. The content may be too long or contain unsupported characters."
        elif error_code == 'ResourceNotFoundException':
            return None, "AI model not found. Please check the AWS Bedrock model configuration."
        else:
            print(f"AWS ClientError ({error_code}): {error_message}")
            return None, f"AI service error: {error_message or 'Failed to generate summary. Please try again.'}"
            
    except BotoCoreError as e:
        print(f"AWS BotoCoreError: {e}")
        return None, "AWS service connection error. Please check your AWS credentials and network connection."
        
    except Exception as e:
        error_str = str(e).lower()
        print(f"Unexpected error in generate_summary: {e}")
        
        # Provide more specific error messages
        if "credentials" in error_str or "token" in error_str:
            return None, "AWS credentials are missing or expired. Please configure your AWS credentials."
        elif "region" in error_str:
            return None, "Invalid AWS region configuration. Please check your AWS_DEFAULT_REGION setting."
        else:
            return None, "An unexpected error occurred while generating summary. Please try again."


def extract_highlights(text: str) -> tuple[list[str] | None, str | None]:
    """
    Extracts key highlights from text using AWS Bedrock with Claude 3.7 Sonnet.
    
    Args:
        text: The text content to extract highlights from
        
    Returns:
        A tuple of (highlights_list, error_message) where:
        - highlights_list: List of highlight strings if successful, None if error
        - error_message: None if successful, error description if failed
    """
    # Handle empty or very short content
    if not text or not text.strip():
        return None, "No content available to extract highlights"
    
    # If content is very short, return it as a single highlight
    if len(text.strip()) < 100:
        return [text.strip()], None
    
    # Truncate if content is too long
    truncated_text = _truncate_content(text)
    
    try:
        # Get Bedrock client
        client = _get_bedrock_client()
        
        # Prepare the prompt for Claude
        prompt = f"""Please extract 3-5 key highlights or important points from the following web content.
Return each highlight as a separate bullet point. Focus on the most important and interesting information.

Content:
{truncated_text}

Key Highlights:"""
        
        # Prepare the request body for Claude 3.7 Sonnet
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": BEDROCK_MAX_TOKENS,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        # Invoke the model
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the highlights from Claude's response
        if 'content' in response_body and len(response_body['content']) > 0:
            highlights_text = response_body['content'][0]['text'].strip()
            
            # Parse the highlights (assuming bullet points or numbered list)
            highlights = []
            for line in highlights_text.split('\n'):
                line = line.strip()
                # Remove bullet points, numbers, dashes, etc.
                if line:
                    # Remove common list markers
                    cleaned = line.lstrip('•-*123456789.() ')
                    if cleaned:
                        highlights.append(cleaned)
            
            # Return at least some highlights, or error if none found
            if highlights:
                return highlights, None
            else:
                return None, "No highlights could be extracted"
        else:
            return None, "Failed to extract highlights. Please try again."
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', '')
        
        if error_code == 'AccessDeniedException':
            return None, "AWS credentials are invalid or expired. Please check your AWS configuration."
        elif error_code == 'ThrottlingException':
            return None, "Service is busy due to rate limiting. Please try again in a moment."
        elif error_code == 'ValidationException':
            return None, "Invalid request to AI service. The content may be too long or contain unsupported characters."
        elif error_code == 'ResourceNotFoundException':
            return None, "AI model not found. Please check the AWS Bedrock model configuration."
        else:
            print(f"AWS ClientError ({error_code}): {error_message}")
            return None, f"AI service error: {error_message or 'Failed to extract highlights. Please try again.'}"
            
    except BotoCoreError as e:
        print(f"AWS BotoCoreError: {e}")
        return None, "AWS service connection error. Please check your AWS credentials and network connection."
        
    except Exception as e:
        error_str = str(e).lower()
        print(f"Unexpected error in extract_highlights: {e}")
        
        # Provide more specific error messages
        if "credentials" in error_str or "token" in error_str:
            return None, "AWS credentials are missing or expired. Please configure your AWS credentials."
        elif "region" in error_str:
            return None, "Invalid AWS region configuration. Please check your AWS_DEFAULT_REGION setting."
        else:
            return None, "An unexpected error occurred while extracting highlights. Please try again."
