"""Unit tests for logging utilities."""

import logging
from unittest.mock import MagicMock, patch

import pytest
import structlog

from src.utils.logging import (
    add_context_to_log,
    clear_request_context,
    get_logger,
    request_id_context,
    set_request_context,
    setup_logging,
    user_id_context,
)


class TestLoggingContext:
    """Test logging context management."""
    
    def test_set_request_context(self):
        """Test setting request context."""
        set_request_context(request_id="req_123", user_id="user_456")
        
        assert request_id_context.get() == "req_123"
        assert user_id_context.get() == "user_456"
    
    def test_set_partial_context(self):
        """Test setting partial context."""
        clear_request_context()
        set_request_context(request_id="req_789")
        
        assert request_id_context.get() == "req_789"
        assert user_id_context.get() is None
    
    def test_clear_request_context(self):
        """Test clearing request context."""
        set_request_context(request_id="req_123", user_id="user_456")
        clear_request_context()
        
        assert request_id_context.get() is None
        assert user_id_context.get() is None
    
    def test_add_context_to_log(self):
        """Test adding context to log entries."""
        set_request_context(request_id="req_123", user_id="user_456")
        
        event_dict = {"message": "Test log"}
        updated_dict = add_context_to_log(None, None, event_dict)
        
        assert updated_dict["request_id"] == "req_123"
        assert updated_dict["user_id"] == "user_456"
        assert updated_dict["message"] == "Test log"
    
    def test_add_context_to_log_no_context(self):
        """Test adding context when no context is set."""
        clear_request_context()
        
        event_dict = {"message": "Test log"}
        updated_dict = add_context_to_log(None, None, event_dict)
        
        assert "request_id" not in updated_dict
        assert "user_id" not in updated_dict
        assert updated_dict["message"] == "Test log"


class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    @patch("src.utils.logging.get_settings")
    def test_setup_logging_json_format(self, mock_get_settings):
        """Test setting up logging with JSON format."""
        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "json"
        mock_settings.log_file = None
        mock_get_settings.return_value = mock_settings
        
        setup_logging()
        
        # Check root logger configuration
        assert logging.root.level == logging.INFO
        assert len(logging.root.handlers) == 1
        
        # Verify structlog is configured
        logger = structlog.get_logger()
        assert logger is not None
    
    @patch("src.utils.logging.get_settings")
    def test_setup_logging_text_format(self, mock_get_settings):
        """Test setting up logging with text format."""
        mock_settings = MagicMock()
        mock_settings.log_level = "DEBUG"
        mock_settings.log_format = "text"
        mock_settings.log_file = None
        mock_get_settings.return_value = mock_settings
        
        setup_logging()
        
        assert logging.root.level == logging.DEBUG
    
    @patch("src.utils.logging.get_settings")
    @patch("logging.FileHandler")
    def test_setup_logging_with_file(self, mock_file_handler, mock_get_settings):
        """Test setting up logging with file output."""
        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "json"
        mock_settings.log_file = "/tmp/test.log"
        mock_get_settings.return_value = mock_settings
        
        setup_logging()
        
        # Verify file handler was created
        mock_file_handler.assert_called_once_with("/tmp/test.log")
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test.module")
        
        # Logger should be returned (exact type depends on structlog configuration)
        assert logger is not None


class TestLoggingIntegration:
    """Test logging integration scenarios."""
    
    @patch("src.utils.logging.get_settings")
    def test_logger_with_context(self, mock_get_settings, caplog):
        """Test logger output with context."""
        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "text"
        mock_settings.log_file = None
        mock_get_settings.return_value = mock_settings
        
        setup_logging()
        set_request_context(request_id="req_test_123")
        
        logger = get_logger("test")
        logger.info("Test message", extra_field="value")
        
        # Basic check that logging is working
        assert logger is not None
    
    @patch("src.utils.logging.get_settings")
    def test_logger_error_with_exception(self, mock_get_settings):
        """Test logging errors with exception info."""
        mock_settings = MagicMock()
        mock_settings.log_level = "ERROR"
        mock_settings.log_format = "text"
        mock_settings.log_file = None
        mock_get_settings.return_value = mock_settings
        
        setup_logging()
        logger = get_logger("test")
        
        # Just verify logger can handle exceptions
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error("Error occurred", exc_info=True)
        
        assert logger is not None