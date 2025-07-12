"""Unit tests for MongoDB connection management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.database.mongo.connection import (
    get_mongo_client,
    get_database,
    get_collection,
    mongo_transaction,
    close_mongo_connection,
    ping_mongo,
    Collections,
)


class TestMongoConnection:
    """Test MongoDB connection functionality."""
    
    @patch('src.database.mongo.connection._mongo_client', None)
    @patch('src.database.mongo.connection.MongoClient')
    @patch('src.database.mongo.connection.get_settings')
    def test_get_mongo_client_creation(self, mock_get_settings, mock_mongo_client_class):
        """Test MongoDB client creation with correct parameters."""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings.mongo_url = "mongodb://localhost:27017"
        mock_settings.mongo_max_pool_size = 100
        mock_settings.mongo_min_pool_size = 10
        mock_settings.mongo_max_idle_time_ms = 45000
        mock_settings.mongo_connect_timeout_ms = 10000
        mock_settings.mongo_server_selection_timeout_ms = 30000
        mock_get_settings.return_value = mock_settings
        
        # Setup mock client
        mock_client = Mock()
        mock_admin = Mock()
        mock_admin.command = Mock(return_value={'ok': 1})
        mock_client.admin = mock_admin
        mock_mongo_client_class.return_value = mock_client
        
        # Get client
        client = get_mongo_client()
        
        # Verify client was created with correct parameters
        mock_mongo_client_class.assert_called_once_with(
            "mongodb://localhost:27017",
            maxPoolSize=100,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=30000,
            retryWrites=True,
            retryReads=True,
        )
        
        # Verify ping was called
        mock_admin.command.assert_called_once_with('ping')
        
        assert client == mock_client
    
    @patch('src.database.mongo.connection._mongo_client', None)
    @patch('src.database.mongo.connection.MongoClient')
    @patch('src.database.mongo.connection.get_settings')
    def test_get_mongo_client_connection_failure(self, mock_get_settings, mock_mongo_client_class):
        """Test MongoDB client creation when connection fails."""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings.mongo_url = "mongodb://localhost:27017"
        mock_settings.mongo_max_pool_size = 100
        mock_settings.mongo_min_pool_size = 10
        mock_settings.mongo_max_idle_time_ms = 45000
        mock_settings.mongo_connect_timeout_ms = 10000
        mock_settings.mongo_server_selection_timeout_ms = 30000
        mock_get_settings.return_value = mock_settings
        
        # Setup mock client to fail
        mock_client = Mock()
        mock_admin = Mock()
        mock_admin.command = Mock(side_effect=ConnectionFailure("Connection failed"))
        mock_client.admin = mock_admin
        mock_mongo_client_class.return_value = mock_client
        
        # Verify exception is raised
        with pytest.raises(ConnectionFailure):
            get_mongo_client()
    
    @patch('src.database.mongo.connection._database', None)
    @patch('src.database.mongo.connection.get_mongo_client')
    @patch('src.database.mongo.connection.get_settings')
    def test_get_database(self, mock_get_settings, mock_get_mongo_client):
        """Test getting database instance."""
        # Setup mock settings
        mock_settings = Mock()
        mock_settings.mongo_database = "lumarank"
        mock_get_settings.return_value = mock_settings
        
        # Setup mock client
        mock_client = Mock()
        mock_database = Mock()
        mock_client.__getitem__ = Mock(return_value=mock_database)
        mock_get_mongo_client.return_value = mock_client
        
        # Get database
        db = get_database()
        
        # Verify database was accessed
        mock_client.__getitem__.assert_called_once_with("lumarank")
        assert db == mock_database
    
    @patch('src.database.mongo.connection.get_database')
    def test_get_collection(self, mock_get_database):
        """Test getting collection by name."""
        # Setup mock database
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.__getitem__ = Mock(return_value=mock_collection)
        mock_get_database.return_value = mock_db
        
        # Get collection
        collection = get_collection("test_collection")
        
        # Verify collection was accessed
        mock_db.__getitem__.assert_called_once_with("test_collection")
        assert collection == mock_collection
    
    @patch('src.database.mongo.connection.get_mongo_client')
    def test_mongo_transaction_context_manager(self, mock_get_mongo_client):
        """Test MongoDB transaction context manager."""
        # Setup mock client with session
        mock_client = Mock()
        mock_session = Mock()
        mock_transaction = Mock()
        
        mock_session.start_transaction = Mock(return_value=mock_transaction)
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_transaction.__enter__ = Mock(return_value=mock_transaction)
        mock_transaction.__exit__ = Mock(return_value=None)
        
        mock_client.start_session = Mock(return_value=mock_session)
        mock_get_mongo_client.return_value = mock_client
        
        # Use transaction
        with mongo_transaction() as session:
            assert session == mock_session
        
        # Verify session lifecycle
        mock_client.start_session.assert_called_once()
        mock_session.start_transaction.assert_called_once()
    
    @patch('src.database.mongo.connection._mongo_client')
    def test_close_mongo_connection(self, mock_client):
        """Test closing MongoDB connection."""
        # Call close
        close_mongo_connection()
        
        # Verify client was closed
        if mock_client is not None:
            mock_client.close.assert_called_once()
    
    @patch('src.database.mongo.connection.get_mongo_client')
    def test_ping_mongo_healthy(self, mock_get_mongo_client):
        """Test MongoDB health check when healthy."""
        # Setup mock client
        mock_client = Mock()
        mock_admin = Mock()
        mock_admin.command = Mock(return_value={'ok': 1})
        mock_client.admin = mock_admin
        mock_client.server_info = Mock(return_value={
            'version': '7.0.0',
            'uptime': 3600,
        })
        mock_get_mongo_client.return_value = mock_client
        
        # Check health
        result = ping_mongo()
        
        # Verify result
        assert result['status'] == 'healthy'
        assert result['ping'] == {'ok': 1}
        assert result['version'] == '7.0.0'
        assert result['uptime'] == 3600
    
    @patch('src.database.mongo.connection.get_mongo_client')
    def test_ping_mongo_unhealthy(self, mock_get_mongo_client):
        """Test MongoDB health check when unhealthy."""
        # Setup mock client to fail
        mock_get_mongo_client.side_effect = ConnectionFailure("Connection failed")
        
        # Check health
        result = ping_mongo()
        
        # Verify result
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert 'Connection failed' in result['error']
    
    def test_collections_constants(self):
        """Test Collections class constants."""
        assert Collections.WEBSITE_CRAWL_DATA == "website_crawl_data"