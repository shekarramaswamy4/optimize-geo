# Database Layer

This directory contains the database abstraction layer for LumaRank, supporting both PostgreSQL and MongoDB.

## Architecture

The database layer is organized into two main components:

```
database/
├── __init__.py          # Exports for easy imports
├── postgres/            # PostgreSQL implementation
│   ├── connection.py    # Connection pooling and session management
│   └── models.py        # SQLAlchemy ORM models
└── mongo/               # MongoDB implementation
    ├── connection.py    # MongoDB client and database access
    ├── models.py        # Pydantic models for MongoDB documents
    └── repositories.py  # Repository pattern for data access
```

## PostgreSQL (Relational Data)

### Purpose
Stores structured, relational data:
- User accounts and authentication
- Organizations (entities)
- User memberships and roles
- Audit trails

### Models

#### User
```python
- id: UUID (primary key)
- email: String (unique)
- first_name: String
- last_name: String
- workos_user_id: String (WorkOS integration)
- is_active: Boolean
- created_at/updated_at: Timestamps
```

#### Entity
```python
- id: UUID (primary key)
- name: String
- is_active: Boolean
- created_at/updated_at: Timestamps
```

#### UserMembership
```python
- id: UUID (primary key)
- user_id: UUID (foreign key)
- entity_id: UUID (foreign key)
- role: String (member/admin/owner)
- is_active: Boolean
- created_at/updated_at: Timestamps
```

### Connection Management

- **Connection Pooling**: SQLAlchemy with QueuePool
- **Pool Size**: Configurable (default: 10)
- **Overflow**: Configurable (default: 20)
- **Session Management**: Scoped sessions per request

### Usage Example

```python
from src.database import get_postgres_db, User

# In a FastAPI endpoint
def get_user(db: Session = Depends(get_postgres_db)):
    user = db.query(User).filter(User.email == "test@example.com").first()
    return user
```

## MongoDB (Document Data)

### Purpose
Stores unstructured and semi-structured data:
- Website crawl data
- Analysis results
- SEO metrics
- Generated questions and test results

### Collections

#### website_crawl_data
Stores all data related to website analysis:
- Website content and metadata
- Extracted company information
- Generated SEO questions
- Test results and scoring
- Performance metrics

### Models

#### WebsiteCrawlData
```python
- _id: ObjectId
- website_url: URL
- domain: String
- company_name: String
- crawl_status: Enum (pending/in_progress/completed/failed)
- company_info: Dict (extracted data)
- generated_questions: Dict (SEO questions)
- test_results: List (question test results)
- seo_score: Float (0-1)
- created_by: String (user ID)
- entity_id: String (organization ID)
```

### Repository Pattern

The MongoDB implementation uses the repository pattern for clean data access:

```python
from src.database import WebsiteCrawlDataRepository

# Create repository instance
repo = WebsiteCrawlDataRepository()

# Create new crawl data
crawl_data = repo.create(WebsiteCrawlDataCreate(
    website_url="https://example.com",
    created_by=user_id,
    entity_id=entity_id
))

# Query by URL
existing = repo.get_by_url("https://example.com")

# Update status
repo.update(crawl_id, WebsiteCrawlDataUpdate(
    crawl_status=CrawlStatus.COMPLETED,
    seo_score=0.85
))
```

### Indexes

Optimized indexes for common queries:
- Unique index on `website_url`
- Index on `entity_id` for multi-tenant queries
- Compound index on `entity_id` + `created_at` for recent data
- Text index on `company_name`, `page_title`, `meta_description` for search

## Migrations

### PostgreSQL (Alembic)

```bash
# Create new migration
poetry run alembic revision -m "Add new column"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### MongoDB

MongoDB migrations are handled automatically through model validation and indexes are created on startup.

## Connection Configuration

### PostgreSQL
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
```

### MongoDB
```env
MONGO_URL=mongodb://localhost:27017
MONGO_DATABASE=lumarank
MONGO_MAX_POOL_SIZE=100
MONGO_MIN_POOL_SIZE=10
```

## Best Practices

1. **Use Dependency Injection**: Always use FastAPI's `Depends()` for database sessions
2. **Transaction Management**: PostgreSQL sessions are automatically managed per request
3. **Error Handling**: All database operations include proper error handling
4. **Connection Pooling**: Both databases use connection pooling for performance
5. **Index Management**: Ensure indexes match query patterns
6. **Multi-tenancy**: Always filter by `entity_id` for data isolation

## Testing

### PostgreSQL Tests
```python
# Uses SQLite in-memory database for tests
def test_create_user(test_db):
    user = User(email="test@example.com", ...)
    test_db.add(user)
    test_db.commit()
```

### MongoDB Tests
```python
# Mock repository for unit tests
@patch("src.database.mongo.repositories.WebsiteCrawlDataRepository")
def test_create_crawl_data(mock_repo):
    mock_repo.create.return_value = MagicMock(id="123")
```

## Performance Considerations

1. **Connection Pooling**: Both databases use connection pooling
2. **Lazy Loading**: SQLAlchemy relationships use lazy loading
3. **Batch Operations**: Use bulk operations for multiple documents
4. **Index Usage**: Monitor slow queries and add indexes as needed
5. **Query Optimization**: Use projections in MongoDB to limit data transfer

## Monitoring

- Connection pool metrics available via logging
- Slow query logging enabled in development
- Database health checks in `/health` endpoint