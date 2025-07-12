"""Unit tests for database connection pool and utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool

from src.db import get_connection, get_session, get_db, init_db, dispose_engine


class TestDatabaseConnectionPool:
    """Test database connection pool functionality."""
    
    def test_engine_creation(self):
        """Test that engine is created with correct parameters."""
        # This test verifies the engine exists and has the right type
        from src.db import engine
        
        assert engine is not None
        assert isinstance(engine, Engine)
        
        # Verify pool class
        assert isinstance(engine.pool, QueuePool)
    
    @patch('src.db.engine')
    def test_get_connection_context_manager(self, mock_engine):
        """Test get_connection context manager."""
        # Setup mock connection
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        
        # Test context manager
        with get_connection() as conn:
            assert conn == mock_connection
        
        # Verify connection lifecycle
        mock_engine.connect.assert_called_once()
        mock_connection.close.assert_called_once()
    
    @patch('src.db.engine')
    def test_get_connection_exception_handling(self, mock_engine):
        """Test get_connection handles exceptions properly."""
        # Setup mock connection
        mock_connection = Mock()
        mock_engine.connect.return_value = mock_connection
        
        # Test exception handling
        with pytest.raises(ValueError):
            with get_connection() as conn:
                raise ValueError("Test error")
        
        # Verify connection is still closed
        mock_connection.close.assert_called_once()
    
    @patch('src.db.SessionLocal')
    def test_get_session_context_manager(self, mock_session_local):
        """Test get_session context manager."""
        # Setup mock session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Test context manager
        with get_session() as session:
            assert session == mock_session
        
        # Verify session lifecycle
        mock_session_local.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('src.db.SessionLocal')
    def test_get_session_exception_handling(self, mock_session_local):
        """Test get_session handles exceptions properly."""
        # Setup mock session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Test exception handling
        with pytest.raises(ValueError):
            with get_session() as session:
                raise ValueError("Test error")
        
        # Verify session is still closed
        mock_session.close.assert_called_once()
    
    @patch('src.db.SessionLocal')
    def test_get_db_generator(self, mock_session_local):
        """Test get_db generator for FastAPI dependency."""
        # Setup mock session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Test generator
        db_gen = get_db()
        db = next(db_gen)
        
        assert db == mock_session
        mock_session_local.assert_called_once()
        
        # Test cleanup
        with pytest.raises(StopIteration):
            next(db_gen)
        
        mock_session.close.assert_called_once()
    
    @patch('src.db.SessionLocal')
    def test_get_db_exception_handling(self, mock_session_local):
        """Test get_db handles exceptions during cleanup."""
        # Setup mock session
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session
        
        # Test generator with exception
        db_gen = get_db()
        db = next(db_gen)
        
        # Simulate exception and cleanup
        try:
            db_gen.throw(ValueError("Test error"))
        except ValueError:
            pass
        
        # Verify session is closed even with exception
        mock_session.close.assert_called_once()
    
    @patch('src.db.engine')
    @patch('src.models.database.Base')
    def test_init_db(self, mock_base, mock_engine):
        """Test database initialization."""
        # Setup mock metadata
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata
        
        # Call init_db
        init_db()
        
        # Verify tables are created
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('src.db.engine')
    def test_dispose_engine(self, mock_engine):
        """Test engine disposal."""
        # Call dispose_engine
        dispose_engine()
        
        # Verify engine is disposed
        mock_engine.dispose.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    @pytest.mark.integration
    def test_real_connection_pool(self):
        """Test real connection pool behavior (requires test database)."""
        # This test requires DATABASE_URL to point to a test database
        # It's marked as integration and will be skipped in unit test runs
        pytest.skip("Integration test - requires test database")
    
    @pytest.mark.integration
    def test_concurrent_connections(self):
        """Test concurrent connection handling."""
        # This test would verify pool behavior under load
        pytest.skip("Integration test - requires test database")