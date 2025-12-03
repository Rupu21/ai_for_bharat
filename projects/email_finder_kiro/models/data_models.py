"""
Core data models for the Email Insights Dashboard.

This module defines the data structures used throughout the application
for representing emails, analysis results, and related entities.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class AnalysisMethod(Enum):
    """Enumeration of available analysis methods."""
    LLM = "llm"
    NLP = "nlp"


@dataclass
class Email:
    """
    Represents an email message retrieved from Gmail.
    
    Attributes:
        id: Unique identifier for the email
        subject: Email subject line
        sender: Display name of the sender
        sender_email: Email address of the sender
        body: Full text content of the email
        timestamp: When the email was received
        snippet: Short preview of the email content
    """
    id: str
    subject: str
    sender: str
    sender_email: str
    body: str
    timestamp: datetime
    snippet: str


@dataclass
class ImportantEmail:
    """
    Represents an email identified as important by analysis.
    
    Attributes:
        email: The Email object
        importance_score: Numerical score indicating importance (0.0-1.0)
        reason: Explanation of why this email is considered important
    """
    email: Email
    importance_score: float
    reason: str


@dataclass
class AnalysisResult:
    """
    Contains the results of email analysis.
    
    Attributes:
        summary: Text summary of all analyzed emails
        important_emails: List of emails flagged as important
        total_unread: Total count of unread emails analyzed
        analysis_method: Method used for analysis (llm or nlp)
        timestamp: When the analysis was performed
    """
    summary: str
    important_emails: List[ImportantEmail]
    total_unread: int
    analysis_method: str
    timestamp: datetime
