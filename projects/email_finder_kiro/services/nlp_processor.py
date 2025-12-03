"""
NLP Processor for email analysis using traditional natural language processing.

This module provides NLP-based analysis of emails using NLTK for keyword extraction,
heuristic-based importance scoring, and extractive summarization techniques.
"""

from datetime import datetime
from typing import List, Set
import re
from collections import Counter

# NLTK imports
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.probability import FreqDist

from models.data_models import Email, AnalysisResult, ImportantEmail


class NLPProcessor:
    """
    Processes emails using traditional NLP techniques.
    
    This processor:
    - Extracts keywords using NLTK
    - Calculates importance scores based on heuristics
    - Generates summaries using extractive methods
    """
    
    # Importance keywords that indicate urgency or priority
    IMPORTANCE_KEYWORDS = {
        'urgent', 'important', 'deadline', 'asap', 'critical', 'priority',
        'action required', 'time sensitive', 'immediate', 'emergency',
        'attention', 'required', 'respond', 'reply', 'confirm', 'approval'
    }
    
    # Work-related domains that might indicate higher importance
    WORK_DOMAINS = {
        'company', 'corp', 'work', 'office', 'business', 'enterprise'
    }
    
    # Importance threshold for flagging emails
    IMPORTANCE_THRESHOLD = 0.5
    
    def __init__(self):
        """
        Initialize NLP Processor and download required NLTK data.
        """
        self._ensure_nltk_data()
        
        # Load stopwords for keyword extraction
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            # Fallback to basic stopwords if download fails
            self.stop_words = {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
                'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
                'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
                'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
                'against', 'between', 'into', 'through', 'during', 'before',
                'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in',
                'out', 'on', 'off', 'over', 'under', 'again', 'further',
                'then', 'once'
            }
    
    def _ensure_nltk_data(self):
        """
        Ensures required NLTK data packages are downloaded.
        """
        required_packages = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
        
        for package in required_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
            except LookupError:
                try:
                    nltk.download(package, quiet=True)
                except Exception:
                    # Continue even if download fails - we have fallbacks
                    pass
    
    def process_emails(self, emails: List[Email]) -> AnalysisResult:
        """
        Analyzes emails using traditional NLP techniques.
        
        Args:
            emails: List of Email objects to analyze
            
        Returns:
            AnalysisResult: Analysis results with summary and important emails
        """
        if not emails:
            return AnalysisResult(
                summary="No unread emails found.",
                important_emails=[],
                total_unread=0,
                analysis_method="nlp",
                timestamp=datetime.now()
            )
        
        # Calculate importance scores for all emails
        important_emails = []
        for email in emails:
            importance_score = self._calculate_importance(email)
            
            # Flag emails above threshold as important
            if importance_score > self.IMPORTANCE_THRESHOLD:
                reason = self._generate_importance_reason(email, importance_score)
                important_emails.append(
                    ImportantEmail(
                        email=email,
                        importance_score=importance_score,
                        reason=reason
                    )
                )
        
        # Sort important emails by score (highest first)
        important_emails.sort(key=lambda x: x.importance_score, reverse=True)
        
        # Generate summary
        summary = self._generate_summary(emails)
        
        return AnalysisResult(
            summary=summary,
            important_emails=important_emails,
            total_unread=len(emails),
            analysis_method="nlp",
            timestamp=datetime.now()
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extracts important keywords from text using NLTK.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List[str]: List of extracted keywords
        """
        if not text:
            return []
        
        # Convert to lowercase for processing
        text_lower = text.lower()
        
        try:
            # Tokenize text
            tokens = word_tokenize(text_lower)
        except Exception:
            # Fallback to simple split if tokenization fails
            tokens = text_lower.split()
        
        # Filter out stopwords and non-alphabetic tokens
        keywords = [
            word for word in tokens
            if word.isalpha() and word not in self.stop_words and len(word) > 2
        ]
        
        # Get frequency distribution
        freq_dist = FreqDist(keywords)
        
        # Return top keywords (up to 10)
        return [word for word, _ in freq_dist.most_common(10)]
    
    def _calculate_importance(self, email: Email) -> float:
        """
        Calculates importance score for an email using heuristic rules.
        
        The score is based on:
        - Presence of importance keywords (urgent, deadline, etc.)
        - Sender domain (work vs personal)
        - Email length (longer emails may be more substantial)
        
        Args:
            email: Email object to score
            
        Returns:
            float: Importance score between 0.0 and 1.0
        """
        score = 0.0
        
        # Combine subject and body for analysis
        full_text = f"{email.subject} {email.body}".lower()
        
        # 1. Check for importance keywords (up to 0.5 points)
        keyword_matches = 0
        for keyword in self.IMPORTANCE_KEYWORDS:
            if keyword in full_text:
                keyword_matches += 1
        
        # Scale keyword score (max 0.5)
        keyword_score = min(keyword_matches * 0.15, 0.5)
        score += keyword_score
        
        # 2. Check sender domain (up to 0.3 points)
        sender_email_lower = email.sender_email.lower()
        
        # Check if from work domain
        is_work_email = any(domain in sender_email_lower for domain in self.WORK_DOMAINS)
        
        # Check if from common personal domains (lower importance)
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        is_personal = any(domain in sender_email_lower for domain in personal_domains)
        
        if is_work_email:
            score += 0.3
        elif not is_personal:
            # Unknown domain - might be work-related
            score += 0.15
        
        # 3. Email length factor (up to 0.2 points)
        # Longer emails might contain more substantial content
        body_length = len(email.body)
        
        if body_length > 1000:
            score += 0.2
        elif body_length > 500:
            score += 0.15
        elif body_length > 200:
            score += 0.1
        elif body_length > 50:
            score += 0.05
        
        # Ensure score is between 0 and 1
        return min(max(score, 0.0), 1.0)
    
    def _generate_importance_reason(self, email: Email, score: float) -> str:
        """
        Generates a human-readable reason for why an email is important.
        
        Args:
            email: Email object
            score: Calculated importance score
            
        Returns:
            str: Explanation of importance
        """
        reasons = []
        
        # Check for keywords
        full_text = f"{email.subject} {email.body}".lower()
        found_keywords = [kw for kw in self.IMPORTANCE_KEYWORDS if kw in full_text]
        
        if found_keywords:
            reasons.append(f"Contains keywords: {', '.join(found_keywords[:3])}")
        
        # Check sender domain
        sender_email_lower = email.sender_email.lower()
        is_work_email = any(domain in sender_email_lower for domain in self.WORK_DOMAINS)
        
        if is_work_email:
            reasons.append("From work-related domain")
        
        # Check length
        if len(email.body) > 1000:
            reasons.append("Substantial content length")
        
        if not reasons:
            reasons.append(f"Importance score: {score:.2f}")
        
        return "; ".join(reasons)
    
    def _generate_summary(self, emails: List[Email]) -> str:
        """
        Generates a summary of emails using extractive summarization.
        
        This method:
        - Identifies common themes/keywords across emails
        - Counts emails by sender
        - Provides overview statistics
        
        Args:
            emails: List of Email objects
            
        Returns:
            str: Summary text
        """
        if not emails:
            return "No unread emails found."
        
        total_count = len(emails)
        
        # Extract all keywords from all emails
        all_keywords = []
        for email in emails:
            text = f"{email.subject} {email.body}"
            keywords = self._extract_keywords(text)
            all_keywords.extend(keywords)
        
        # Get top themes
        keyword_freq = Counter(all_keywords)
        top_themes = [word for word, _ in keyword_freq.most_common(5)]
        
        # Count unique senders
        senders = set(email.sender for email in emails)
        sender_count = len(senders)
        
        # Get top senders
        sender_freq = Counter(email.sender for email in emails)
        top_senders = [sender for sender, _ in sender_freq.most_common(3)]
        
        # Build summary
        summary_parts = [
            f"You have {total_count} unread email{'s' if total_count != 1 else ''} from {sender_count} sender{'s' if sender_count != 1 else ''}."
        ]
        
        if top_senders:
            summary_parts.append(
                f"Most emails are from: {', '.join(top_senders)}."
            )
        
        if top_themes:
            summary_parts.append(
                f"Common themes include: {', '.join(top_themes)}."
            )
        
        # Add time-based insight
        try:
            # Handle both timezone-aware and timezone-naive datetimes
            from datetime import timezone
            now = datetime.now(timezone.utc)
            recent_emails = []
            for e in emails:
                # Make timestamp timezone-aware if it isn't
                email_time = e.timestamp
                if email_time.tzinfo is None:
                    email_time = email_time.replace(tzinfo=timezone.utc)
                if (now - email_time).days < 1:
                    recent_emails.append(e)
            
            if recent_emails:
                summary_parts.append(
                    f"{len(recent_emails)} email{'s' if len(recent_emails) != 1 else ''} received in the last 24 hours."
                )
        except Exception:
            # Skip time-based insight if there's any datetime issue
            pass
        
        return " ".join(summary_parts)
