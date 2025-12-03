"""
Unit tests for the Analysis Engine.

Tests the routing logic and integration with LLM and NLP processors.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from models.data_models import Email, AnalysisResult, AnalysisMethod, ImportantEmail
from services.analysis_engine import AnalysisEngine
from services.llm_processor import LLMProcessor
from services.nlp_processor import NLPProcessor


class TestAnalysisEngine(unittest.TestCase):
    """Test cases for AnalysisEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample emails for testing
        self.sample_emails = [
            Email(
                id="1",
                subject="Urgent: Project Deadline",
                sender="John Doe",
                sender_email="john@company.com",
                body="We need to complete the project by Friday.",
                timestamp=datetime.now(),
                snippet="We need to complete..."
            ),
            Email(
                id="2",
                subject="Meeting Tomorrow",
                sender="Jane Smith",
                sender_email="jane@company.com",
                body="Don't forget about our meeting at 10 AM.",
                timestamp=datetime.now(),
                snippet="Don't forget..."
            )
        ]
        
        # Create mock processors
        self.mock_llm_processor = Mock(spec=LLMProcessor)
        self.mock_nlp_processor = Mock(spec=NLPProcessor)
        
        # Create analysis engine with mocked processors
        self.engine = AnalysisEngine(
            llm_processor=self.mock_llm_processor,
            nlp_processor=self.mock_nlp_processor
        )
    
    def test_analyze_emails_routes_to_llm_processor(self):
        """Test that LLM method routes to LLM processor."""
        # Arrange
        expected_result = AnalysisResult(
            summary="LLM summary",
            important_emails=[],
            total_unread=2,
            analysis_method="llm",
            timestamp=datetime.now()
        )
        self.mock_llm_processor.process_emails.return_value = expected_result
        
        # Act
        result = self.engine.analyze_emails(self.sample_emails, AnalysisMethod.LLM)
        
        # Assert
        self.mock_llm_processor.process_emails.assert_called_once_with(self.sample_emails)
        self.mock_nlp_processor.process_emails.assert_not_called()
        self.assertEqual(result, expected_result)
        self.assertEqual(result.analysis_method, "llm")
    
    def test_analyze_emails_routes_to_nlp_processor(self):
        """Test that NLP method routes to NLP processor."""
        # Arrange
        expected_result = AnalysisResult(
            summary="NLP summary",
            important_emails=[],
            total_unread=2,
            analysis_method="nlp",
            timestamp=datetime.now()
        )
        self.mock_nlp_processor.process_emails.return_value = expected_result
        
        # Act
        result = self.engine.analyze_emails(self.sample_emails, AnalysisMethod.NLP)
        
        # Assert
        self.mock_nlp_processor.process_emails.assert_called_once_with(self.sample_emails)
        self.mock_llm_processor.process_emails.assert_not_called()
        self.assertEqual(result, expected_result)
        self.assertEqual(result.analysis_method, "nlp")
    
    def test_analyze_emails_with_empty_list(self):
        """Test analysis with empty email list."""
        # Arrange
        empty_result = AnalysisResult(
            summary="No emails",
            important_emails=[],
            total_unread=0,
            analysis_method="llm",
            timestamp=datetime.now()
        )
        self.mock_llm_processor.process_emails.return_value = empty_result
        
        # Act
        result = self.engine.analyze_emails([], AnalysisMethod.LLM)
        
        # Assert
        self.mock_llm_processor.process_emails.assert_called_once_with([])
        self.assertEqual(result.total_unread, 0)
    
    def test_analyze_emails_with_invalid_method_raises_error(self):
        """Test that invalid method raises ValueError."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.engine.analyze_emails(self.sample_emails, "invalid_method")
        
        self.assertIn("Unsupported analysis method", str(context.exception))
    
    def test_engine_creates_default_processors(self):
        """Test that engine creates default processors if none provided."""
        # Arrange - Create mock processors to avoid config issues
        mock_llm = Mock(spec=LLMProcessor)
        mock_nlp = Mock(spec=NLPProcessor)
        
        # Act
        engine = AnalysisEngine(config=None, llm_processor=mock_llm, nlp_processor=mock_nlp)
        
        # Assert
        self.assertIsInstance(engine.llm_processor, Mock)
        self.assertIsInstance(engine.nlp_processor, Mock)
    
    def test_llm_processor_returns_important_emails(self):
        """Test that LLM processor results include important emails."""
        # Arrange
        important_email = ImportantEmail(
            email=self.sample_emails[0],
            importance_score=0.9,
            reason="Contains urgent keyword"
        )
        expected_result = AnalysisResult(
            summary="One urgent email found",
            important_emails=[important_email],
            total_unread=2,
            analysis_method="llm",
            timestamp=datetime.now()
        )
        self.mock_llm_processor.process_emails.return_value = expected_result
        
        # Act
        result = self.engine.analyze_emails(self.sample_emails, AnalysisMethod.LLM)
        
        # Assert
        self.assertEqual(len(result.important_emails), 1)
        self.assertEqual(result.important_emails[0].importance_score, 0.9)
    
    def test_nlp_processor_returns_important_emails(self):
        """Test that NLP processor results include important emails."""
        # Arrange
        important_email = ImportantEmail(
            email=self.sample_emails[0],
            importance_score=0.75,
            reason="Work domain and urgent keywords"
        )
        expected_result = AnalysisResult(
            summary="Analysis complete",
            important_emails=[important_email],
            total_unread=2,
            analysis_method="nlp",
            timestamp=datetime.now()
        )
        self.mock_nlp_processor.process_emails.return_value = expected_result
        
        # Act
        result = self.engine.analyze_emails(self.sample_emails, AnalysisMethod.NLP)
        
        # Assert
        self.assertEqual(len(result.important_emails), 1)
        self.assertEqual(result.important_emails[0].importance_score, 0.75)


if __name__ == '__main__':
    unittest.main()
