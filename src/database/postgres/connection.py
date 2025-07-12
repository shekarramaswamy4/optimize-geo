"""Database connection management with SQLAlchemy and connection pooling."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from src.config.settings import get_settings

# Get settings
settings = get_settings()

# Create engine with connection pooling
engine: Engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_recycle=settings.database_pool_recycle,
    pool_pre_ping=True,  # Test connections before using
    echo=settings.database_echo,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """
    Get a raw database connection from the pool.
    
    Usage:
        with get_connection() as conn:
            result = conn.execute("SELECT 1")
    
    Yields:
        Connection: SQLAlchemy connection object
    """
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a SQLAlchemy session for ORM operations.
    
    Usage:
        with get_session() as session:
            users = session.query(User).all()
    
    Yields:
        Session: SQLAlchemy session object
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    
    Yields:
        Session: SQLAlchemy session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (useful for creating tables in development)."""
    # Import all models here to ensure they are registered with SQLAlchemy
    from src.database.postgres.models import Base
    
    Base.metadata.create_all(bind=engine)


def dispose_engine() -> None:
    """Dispose of the connection pool (useful for cleanup)."""
    engine.dispose()