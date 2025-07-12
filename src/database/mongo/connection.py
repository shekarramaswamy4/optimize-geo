"""MongoDB connection management with connection pooling."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Global MongoDB client instance
_mongo_client: Optional[MongoClient] = None
_database: Optional[Database] = None


def get_mongo_client() -> MongoClient:
    """
    Get or create MongoDB client with connection pooling.
    
    Returns:
        MongoClient: MongoDB client instance
    """
    global _mongo_client
    
    if _mongo_client is None:
        settings = get_settings()
        
        # MongoDB connection options
        options = {
            "maxPoolSize": settings.mongo_max_pool_size,
            "minPoolSize": settings.mongo_min_pool_size,
            "maxIdleTimeMS": settings.mongo_max_idle_time_ms,
            "connectTimeoutMS": settings.mongo_connect_timeout_ms,
            "serverSelectionTimeoutMS": settings.mongo_server_selection_timeout_ms,
            "retryWrites": True,
            "retryReads": True,
        }
        
        _mongo_client = MongoClient(settings.mongo_url, **options)
        
        # Test connection
        try:
            _mongo_client.admin.command('ping')
            logger.info("MongoDB connection established successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    return _mongo_client


def get_database() -> Database:
    """
    Get MongoDB database instance.
    
    Returns:
        Database: MongoDB database instance
    """
    global _database
    
    if _database is None:
        settings = get_settings()
        client = get_mongo_client()
        _database = client[settings.mongo_database]
    
    return _database


def get_collection(collection_name: str) -> Collection:
    """
    Get MongoDB collection by name.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection: MongoDB collection instance
    """
    db = get_database()
    return db[collection_name]


@contextmanager
def mongo_transaction():
    """
    Context manager for MongoDB transactions.
    
    Usage:
        with mongo_transaction() as session:
            collection.insert_one(doc, session=session)
    """
    client = get_mongo_client()
    with client.start_session() as session:
        with session.start_transaction():
            yield session


def close_mongo_connection():
    """Close MongoDB connection and cleanup."""
    global _mongo_client, _database
    
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _database = None
        logger.info("MongoDB connection closed")


def ping_mongo() -> Dict[str, Any]:
    """
    Check MongoDB connection health.
    
    Returns:
        Dict with connection status
    """
    try:
        client = get_mongo_client()
        result = client.admin.command('ping')
        server_info = client.server_info()
        
        return {
            "status": "healthy",
            "ping": result,
            "version": server_info.get("version"),
            "uptime": server_info.get("uptime"),
        }
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# Collections
class Collections:
    """MongoDB collection names."""
    WEBSITE_CRAWL_DATA = "website_crawl_data"