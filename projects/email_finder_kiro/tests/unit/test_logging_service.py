"""
Unit tests for LoggingService.

Tests the logging functionality including input logging, output logging,
email retrieval logging, error logging, and log persistence.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime
from services.logging_service import LoggingService


@pytest.fixture
def temp_log_file():
    """Fixture to create a temporary log file for testing."""
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.log')
    os.close(fd)
    yield path
    # Cleanup after test - no need to remove, temp files will be cleaned up by OS


@pytest.fixture
def logging_service(temp_log_file):
    """Fixture to create a LoggingService instance with temporary log file."""
    service = LoggingService(log_file_path=temp_log_file)
    yield service
    # Close all handlers to release file locks
    for handler in service.logger.handlers[:]:
        handler.close()
        service.logger.removeHandler(handler)


def test_logging_service_initialization(temp_log_file):
    """Test that LoggingService initializes correctly with specified log file."""
    ls = LoggingService(log_file_path=temp_log_file)
    assert ls.log_file_path == temp_log_file
    assert ls.logger is not None
    assert ls.logger.name == 'EmailInsightsDashboard'


def test_logging_service_creates_log_directory():
    """Test that LoggingService creates log directory if it doesn't exist."""
    # Use a path in a non-existent directory
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, 'subdir', 'test.log')
        ls = LoggingService(log_file_path=log_path)
        
        # Verify directory was created
        assert os.path.exists(os.path.dirname(log_path))
        
        # Close handlers to release file locks
        for handler in ls.logger.handlers[:]:
            handler.close()
            ls.logger.removeHandler(handler)


def test_log_input(logging_service, temp_log_file):
    """Test logging user input with timestamp and user_id."""
    user_id = 'user123'
    input_data = {'days_back': 7, 'method': 'llm'}
    
    logging_service.log_input(user_id, input_data)
    
    # Read log file and verify content
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'USER_INPUT' in log_content
    assert user_id in log_content
    assert 'days_back' in log_content
    assert 'llm' in log_content
    assert 'timestamp' in log_content


def test_log_output(logging_service, temp_log_file):
    """Test logging system output with timestamp and input reference."""
    user_id = 'user456'
    output_data = {'summary': 'Test summary', 'important_count': 5}
    input_ref = 'input_ref_123'
    
    logging_service.log_output(user_id, output_data, input_ref)
    
    # Read log file and verify content
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'SYSTEM_OUTPUT' in log_content
    assert user_id in log_content
    assert input_ref in log_content
    assert 'Test summary' in log_content
    assert 'timestamp' in log_content


def test_log_email_retrieval(logging_service, temp_log_file):
    """Test logging email retrieval operation with count and time range."""
    user_id = 'user789'
    count = 42
    days_back = 7
    
    logging_service.log_email_retrieval(user_id, count, days_back)
    
    # Read log file and verify content
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'EMAIL_RETRIEVAL' in log_content
    assert user_id in log_content
    assert str(count) in log_content
    assert str(days_back) in log_content
    assert 'timestamp' in log_content


def test_log_error(logging_service, temp_log_file):
    """Test logging errors with stack trace and context."""
    context = {'user_id': 'user999', 'operation': 'test_operation'}
    
    try:
        raise ValueError("Test error message")
    except Exception as e:
        logging_service.log_error(e, context)
    
    # Read log file and verify content
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'ERROR' in log_content
    assert 'ValueError' in log_content
    assert 'Test error message' in log_content
    assert 'stack_trace' in log_content
    assert 'user999' in log_content
    assert 'test_operation' in log_content


def test_log_persistence(logging_service, temp_log_file):
    """Test that logs are persisted to file and can be retrieved."""
    # Log multiple entries
    logging_service.log_input('user1', {'test': 'data1'})
    logging_service.log_output('user2', {'result': 'data2'}, 'ref1')
    logging_service.log_email_retrieval('user3', 10, 5)
    
    # Verify file exists
    assert os.path.exists(temp_log_file)
    
    # Verify file has content
    with open(temp_log_file, 'r') as f:
        content = f.read()
    
    assert len(content) > 0
    assert 'USER_INPUT' in content
    assert 'SYSTEM_OUTPUT' in content
    assert 'EMAIL_RETRIEVAL' in content


def test_multiple_log_entries(logging_service, temp_log_file):
    """Test that multiple log entries are written correctly."""
    # Log multiple entries of different types
    for i in range(3):
        logging_service.log_input(f'user{i}', {'iteration': i})
    
    # Read and count entries
    with open(temp_log_file, 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
    
    # Should have 3 log entries
    assert len(lines) >= 3
    assert content.count('USER_INPUT') == 3


def test_log_input_with_complex_data(logging_service, temp_log_file):
    """Test logging with complex nested data structures."""
    complex_data = {
        'days_back': 30,
        'method': 'llm',
        'filters': {
            'sender': 'test@example.com',
            'keywords': ['urgent', 'important']
        }
    }
    
    logging_service.log_input('user_complex', complex_data)
    
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'user_complex' in log_content
    assert 'filters' in log_content
    assert 'urgent' in log_content


def test_log_error_with_nested_exception(logging_service, temp_log_file):
    """Test logging errors with nested exception context."""
    try:
        try:
            raise ValueError("Inner error")
        except ValueError:
            raise RuntimeError("Outer error")
    except Exception as e:
        logging_service.log_error(e, {'nested': True})
    
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    assert 'RuntimeError' in log_content
    assert 'Outer error' in log_content
    assert 'stack_trace' in log_content


def test_default_log_path():
    """Test that LoggingService uses default log path when none specified."""
    ls = LoggingService()
    # Should use default or environment variable
    assert ls.log_file_path is not None
    assert isinstance(ls.log_file_path, str)
