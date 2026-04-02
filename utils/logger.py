"""
Logger configuration module using loguru.

This module provides a centralized logging configuration for the application,
with structured logs sent to both console and a rotating file.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger() -> None:
    """
    Configure loguru logger with console and file handlers.
    
    Sets up:
    - Console output with INFO level and colored formatting
    - File output with rotation, retention, and compression
    """
    # Remove default logger
    logger.remove()
    
    # Add console handler with colored output
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Add file handler with rotation
    logger.add(
        "logs/scraper.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="30 days",  # Keep logs for 30 days
        compression="zip",  # Compress rotated logs
        enqueue=True,  # Thread-safe logging
    )


# Initialize logger on import
setup_logger()


def get_logger():
    """
    Get the configured logger instance.
    
    Returns:
        Logger: The configured loguru logger instance
    """
    return logger
