"""
Analysis Engine for routing email analysis to appropriate processors.

This module provides the main analysis coordination, routing requests
to either LLM or NLP processors based on the selected method.
"""

from typing import List, Optional

from models.data_models import Email, AnalysisResult, AnalysisMethod
from services.llm_processor import LLMProcessor
from services.nlp_processor import NLPProcessor


class AnalysisEngine:
    """
    Coordinates email analysis by routing to appropriate processors.
    
    This engine:
    - Accepts analysis requests with method specification
    - Routes to LLMProcessor for LLM-based analysis
    - Routes to NLPProcessor for traditional NLP analysis
    - Returns structured AnalysisResult from selected processor
    """
    
    def __init__(self, config=None, llm_processor: LLMProcessor = None, nlp_processor: NLPProcessor = None):
        """
        Initialize Analysis Engine with processors.
        
        Args:
            config: Optional Config instance to pass to processors.
            llm_processor: Optional LLMProcessor instance. If not provided,
                          a new instance will be created.
            nlp_processor: Optional NLPProcessor instance. If not provided,
                          a new instance will be created.
        """
        self.config = config
        self.llm_processor = llm_processor if llm_processor else LLMProcessor(config)
        self.nlp_processor = nlp_processor if nlp_processor else NLPProcessor()
    
    def analyze_emails(self, emails: List[Email], method: AnalysisMethod) -> AnalysisResult:
        """
        Analyzes emails using the specified method.
        
        Routes the analysis request to the appropriate processor based on
        the method parameter. Supports both LLM and NLP analysis methods.
        
        Args:
            emails: List of Email objects to analyze
            method: AnalysisMethod enum specifying LLM or NLP
            
        Returns:
            AnalysisResult: Analysis results from the selected processor
            
        Raises:
            ValueError: If an unsupported analysis method is provided
        """
        if method == AnalysisMethod.LLM:
            # Route to LLM Processor
            return self.llm_processor.process_emails(emails)
        elif method == AnalysisMethod.NLP:
            # Route to NLP Processor
            return self.nlp_processor.process_emails(emails)
        else:
            raise ValueError(f"Unsupported analysis method: {method}")
