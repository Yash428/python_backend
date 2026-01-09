"""
Utility functions for Jitsi Transcriber.

This module provides helper functions for time conversion, logging, and file operations.
"""

import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional


def setup_logger(name: str) -> logging.Logger:
    """
    Setup and return a logger with console output.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted timestamp string (HH:MM:SS.mmm)
    """
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert HH:MM:SS.mmm format to seconds.
    
    Args:
        timestamp: Formatted timestamp string (HH:MM:SS.mmm)
        
    Returns:
        Time in seconds
    """
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    
    # Handle seconds and milliseconds
    sec_parts = parts[2].split('.')
    seconds = int(sec_parts[0])
    milliseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to directory
        
    Returns:
        The path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent


def validate_file_exists(file_path: Path) -> bool:
    """
    Check if a file exists and log appropriate message.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    if not file_path.exists():
        logger = setup_logger(__name__)
        logger.error(f"File not found: {file_path}")
        return False
    return True


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def safe_filename(text: str, max_length: int = 200) -> str:
    """
    Convert text to a safe filename.
    
    Args:
        text: Original text
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
    """
    import re
    
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    return filename


if __name__ == "__main__":
    # Quick test
    logger = setup_logger(__name__)
    
    test_seconds = 125.456
    ts = seconds_to_timestamp(test_seconds)
    logger.info(f"Converted {test_seconds}s to timestamp: {ts}")
    
    back_to_seconds = timestamp_to_seconds(ts)
    logger.info(f"Converted back to: {back_to_seconds}s")
    
    duration_str = format_duration(3665)
    logger.info(f"3665 seconds formatted: {duration_str}")
