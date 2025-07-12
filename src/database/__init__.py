"""Database package with PostgreSQL and MongoDB support."""

# PostgreSQL exports
from src.database.postgres.connection import (
    get_connection as get_postgres_connection,
    get_session as get_postgres_session,
    get_db as get_postgres_db,
    init_db as init_postgres_db,
    dispose_engine as dispose_postgres_engine,
)
from src.database.postgres.models import User, Entity, UserMembership

# MongoDB exports
from src.database.mongo.connection import (
    get_mongo_client,
    get_database as get_mongo_database,
    get_collection as get_mongo_collection,
    mongo_transaction,
    close_mongo_connection,
    ping_mongo,
    Collections,
)
from src.database.mongo.models import (
    WebsiteCrawlData,
    WebsiteCrawlDataCreate,
    WebsiteCrawlDataUpdate,
    CrawlStatus,
)
from src.database.mongo.repositories import WebsiteCrawlDataRepository

__all__ = [
    # PostgreSQL
    "get_postgres_connection",
    "get_postgres_session",
    "get_postgres_db",
    "init_postgres_db",
    "dispose_postgres_engine",
    "User",
    "Entity",
    "UserMembership",
    # MongoDB
    "get_mongo_client",
    "get_mongo_database",
    "get_mongo_collection",
    "mongo_transaction",
    "close_mongo_connection",
    "ping_mongo",
    "Collections",
    "WebsiteCrawlData",
    "WebsiteCrawlDataCreate",
    "WebsiteCrawlDataUpdate",
    "CrawlStatus",
    "WebsiteCrawlDataRepository",
]