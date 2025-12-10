"""Logging utilities for the dashboard application."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Set up logging directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("dashboard")


def log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def log_error(message: str, exc_info: bool = False) -> None:
    """Log an error message."""
    logger.error(message, exc_info=exc_info)


def log_warning(message: str) -> None:
    """Log a warning message."""
    logger.warning(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)


def log_mcp_call(
    server_name: str, 
    tool_name: str, 
    args: Optional[Dict[str, Any]] = None,
    arguments: Optional[Dict[str, Any]] = None,
    success: Optional[bool] = None,
    duration_ms: Optional[float] = None,
    result_count: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """Log an MCP call with formatted output."""
    # Use arguments if provided, otherwise use args
    call_args = arguments or args
    args_str = f" with args: {call_args}" if call_args else ""
    
    if success is not None:
        if success:
            status = "✅"
            extra_info = []
            if duration_ms is not None:
                extra_info.append(f"duration: {duration_ms:.2f}ms")
            if result_count is not None:
                extra_info.append(f"results: {result_count}")
            extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
            logger.info(f"{status} MCP Call: {server_name}.{tool_name}{args_str}{extra_str}")
        else:
            status = "❌"
            error_str = f" - Error: {error}" if error else ""
            duration_str = f" (duration: {duration_ms:.2f}ms)" if duration_ms else ""
            logger.error(f"{status} MCP Call Failed: {server_name}.{tool_name}{args_str}{error_str}{duration_str}")
    else:
        logger.info(f"MCP Client: Calling {server_name}.{tool_name}{args_str}")


def sanitize_message(message: str) -> str:
    """Sanitize message for Windows logging compatibility."""
    if not isinstance(message, str):
        message = str(message)
    
    # Replace problematic Unicode characters
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '--', # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2026': '...' # ellipsis
    }
    
    for unicode_char, replacement in replacements.items():
        message = message.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    message = message.encode('ascii', 'ignore').decode('ascii')
    
    return message