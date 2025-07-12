import logging
import sys
from contextvars import ContextVar
from typing import Any, Optional

import structlog
from pythonjsonlogger import jsonlogger

from src.config.settings import get_settings

# Context variables for request tracking
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def add_context_to_log(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add context variables to log entries."""
    request_id = request_id_context.get()
    user_id = user_id_context.get()
    
    if request_id:
        event_dict["request_id"] = request_id
    if user_id:
        event_dict["user_id"] = user_id
    
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
    # Configure standard library logging
    log_level = getattr(logging, settings.log_level.upper())
    
    # Remove default handlers
    logging.root.handlers = []
    
    # Create formatter based on settings
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "name": "logger",
                "levelname": "level",
            },
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # File handler (if configured)
    handlers = [console_handler]
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.root.setLevel(log_level)
    for handler in handlers:
        logging.root.addHandler(handler)
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_context_to_log,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance with the given name."""
    return structlog.get_logger(name)


# Convenience function to set request context
def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None) -> None:
    """Set request context for logging."""
    if request_id is not None:
        request_id_context.set(request_id)
    if user_id is not None:
        user_id_context.set(user_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_context.set(None)
    user_id_context.set(None)