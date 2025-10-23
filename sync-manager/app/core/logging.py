"""
Logging configuration for Sync Manager
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup application logging"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # JSON formatter for structured logging
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'timestamp': '@timestamp', 'level': 'log.level'}
    )
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Use colored formatter for console
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_formatter = logging.Formatter(console_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    
    # Log startup message
    logger.info("Logging configured", extra={
        "log_level": log_level,
        "log_file": log_file
    })
    
    # Suppress noisy loggers
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter to add context"""
    
    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = self.extra
        else:
            kwargs['extra'].update(self.extra)
        return msg, kwargs


def get_logger(name: str, **context) -> LoggerAdapter:
    """Get logger with context"""
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, context)
