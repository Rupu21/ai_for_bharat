"""
Logging Service for Email Insights Dashboard
Handles all logging operations including inputs, outputs, email retrieval, and errors.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
import json

from config import get_config


class LoggingService:
    """
    Service for logging all system operations including user inputs, outputs,
    email retrieval operations, and errors.
    
    Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
    """
    
    def __init__(self, config=None, log_file_path: Optional[str] = None):
        """
        Initialize the logging service with file handler.
        
        Args:
            config: Optional Config instance. If None, uses global config.
            log_file_path: Optional override for log file path. If None, uses config value.
        """
        self.config = config or get_config()
        
        # Use provided path or get from config
        self.log_file_path = log_file_path or self.config.log_file_path
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger('EmailInsightsDashboard')
        
        # Set log level from config
        log_level = getattr(logging, self.config.log_level, logging.INFO)
        self.logger.setLevel(log_level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Create formatter using config settings
        formatter = logging.Formatter(
            self.config.log_format,
            datefmt=self.config.log_date_format
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
    
    def log_input(self, user_id: str, input_data: Dict[str, Any]) -> None:
        """
        Log user input with timestamp and user identifier.
        
        Requirements: 8.1 - WHEN the user provides any input THEN the Logging Service 
        SHALL record the input with a timestamp and user identifier
        
        Args:
            user_id: Unique identifier for the user
            input_data: Dictionary containing the user input data
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'type': 'INPUT',
            'timestamp': timestamp,
            'user_id': user_id,
            'input_data': input_data
        }
        self.logger.info(f"USER_INPUT: {json.dumps(log_entry)}")
    
    def log_output(self, user_id: str, output_data: Dict[str, Any], input_ref: str) -> None:
        """
        Log system output with timestamp and associated input reference.
        
        Requirements: 8.2 - WHEN the Analysis Engine generates any output THEN the 
        Logging Service SHALL record the output with a timestamp and associated input reference
        
        Args:
            user_id: Unique identifier for the user
            output_data: Dictionary containing the output data
            input_ref: Reference to the associated input that generated this output
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'type': 'OUTPUT',
            'timestamp': timestamp,
            'user_id': user_id,
            'input_ref': input_ref,
            'output_data': output_data
        }
        self.logger.info(f"SYSTEM_OUTPUT: {json.dumps(log_entry)}")
    
    def log_email_retrieval(self, user_id: str, count: int, days_back: int) -> None:
        """
        Log email retrieval operation with count and time range.
        
        Requirements: 8.3 - WHEN the Gmail Service retrieves emails THEN the Logging 
        Service SHALL record the number of emails retrieved and the time range used
        
        Args:
            user_id: Unique identifier for the user
            count: Number of emails retrieved
            days_back: Time range in days used for retrieval
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'type': 'EMAIL_RETRIEVAL',
            'timestamp': timestamp,
            'user_id': user_id,
            'emails_retrieved': count,
            'days_back': days_back
        }
        self.logger.info(f"EMAIL_RETRIEVAL: {json.dumps(log_entry)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log error with details including stack trace and context.
        
        Requirements: 8.4 - WHEN any component generates an error THEN the Logging 
        Service SHALL record the error details including stack trace and context
        
        Args:
            error: The exception that occurred
            context: Dictionary containing contextual information about the error
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'type': 'ERROR',
            'timestamp': timestamp,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': context
        }
        self.logger.error(f"ERROR: {json.dumps(log_entry)}")
