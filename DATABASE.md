# Database Setup (PostgreSQL + MongoDB)

This document describes the database architecture for the LumaRank project.

## Architecture

### PostgreSQL
- **SQLAlchemy 2.0** for ORM and connection pooling
- **Alembic** for database migrations using raw SQL files
- **PostgreSQL 16** for relational data (users, entities, memberships)

### MongoDB
- **PyMongo** for database operations
- **MongoDB 7** for document storage (website crawl data)
- **Repository pattern** for clean data access

### Infrastructure
- **Single docker-compose.yml** with profiles for different environments
- **Production-grade connection pooling** for both databases
- **Health checks** and monitoring support

## Quick Start

### 1. Start Databases

```bash
# For local development (PostgreSQL + MongoDB)
make db-up

# Start only PostgreSQL
make postgres-up

# Start only MongoDB
make mongo-up

# For production (web + databases)
make prod-up

# Verify they're running
docker ps
```

### 2. Run Migrations

```bash
# Apply all migrations
make db-migrate

# Check migration status
poetry run alembic current
```

### 3. Access Database

```bash
# PostgreSQL shell
make db-shell

# List tables
\dt

# Describe a table
\d users
```

## Data Models

### PostgreSQL Tables

#### Users Table
- `id` (UUID, primary key)
- `email` (unique)
- `first_name`, `last_name`
- `workos_user_id` (for SSO integration)
- Full audit columns

#### Entity Table
- `id` (UUID, primary key)
- `name`
- Full audit columns

#### User Membership Table
- Links users to entities
- `role` field (default: "member")
- Cascade delete on user/entity removal
- Unique constraint on (user_id, entity_id)

### MongoDB Collections

#### website_crawl_data
- Website analysis and crawl results
- SEO scoring and test results
- Full-text search capabilities
- Document schema:
  ```javascript
  {
    _id: ObjectId,
    website_url: "https://example.com",
    domain: "example.com",
    company_name: "Example Corp",
    crawl_status: "completed",
    crawl_started_at: ISODate(),
    crawl_completed_at: ISODate(),
    crawl_duration_seconds: 5.5,
    page_title: "Example Page",
    meta_description: "...",
    company_info: { /* extracted data */ },
    generated_questions: { /* SEO questions */ },
    test_results: [ /* question test results */ ],
    seo_score: 0.85,
    created_at: ISODate(),
    updated_at: ISODate()
  }
  ```

## Docker Compose Profiles

The single `docker-compose.yml` uses profiles to manage different environments:

- **No profile** (default): Just PostgreSQL for local development
- **`test` profile**: PostgreSQL test database on port 5433
- **`prod` profile**: Full production stack (web + PostgreSQL)
- **`monitoring` profile**: Optional Prometheus and Grafana

## Development Commands

```bash
# Local development
make db-up          # Start all databases
make db-down        # Stop all databases
make postgres-up    # Start only PostgreSQL
make mongo-up       # Start only MongoDB
make db-migrate     # Run PostgreSQL migrations
make db-rollback    # Rollback last migration
make db-reset       # Reset PostgreSQL database
make db-shell       # Open PostgreSQL shell
make mongo-shell    # Open MongoDB shell

# Testing
make db-test-up     # Start test databases
make db-test-down   # Stop test databases
make test-unit      # Run unit tests

# Production
make prod-up        # Start web + databases
make prod-down      # Stop production stack
make prod-logs      # View production logs
```

## Connection Management

### Using Raw SQL
```python
from src.db import get_connection

with get_connection() as conn:
    result = conn.execute("SELECT * FROM users WHERE is_active = true")
    users = result.fetchall()
```

### Using ORM
```python
from src.db import get_session
from src.models.database import User

with get_session() as session:
    users = session.query(User).filter(User.is_active == True).all()
```

### FastAPI Integration
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from src.database import get_postgres_db, User

@app.get("/users")
def get_users(db: Session = Depends(get_postgres_db)):
    return db.query(User).all()
```

### MongoDB Usage

#### Using Repository Pattern
```python
from src.database import WebsiteCrawlDataRepository, WebsiteCrawlDataCreate

# Create repository
repo = WebsiteCrawlDataRepository()

# Create new crawl data
crawl_data = await repo.create(WebsiteCrawlDataCreate(
    website_url="https://example.com",
    company_name="Example Corp"
))

# Get by URL
crawl_data = await repo.get_by_url("https://example.com")

# List with filters
crawl_list = await repo.list(
    status=CrawlStatus.COMPLETED,
    limit=50
)

# Search
search_results = await repo.search("example company")

# Get statistics
stats = await repo.get_statistics()
```

#### Direct MongoDB Access
```python
from src.database import get_mongo_collection, Collections

# Get collection
collection = get_mongo_collection(Collections.WEBSITE_CRAWL_DATA)

# Insert document
result = collection.insert_one({
    "website_url": "https://example.com",
    "crawl_status": "pending"
})

# Find documents
docs = collection.find({"crawl_status": "completed"})
```

## Configuration

Database settings in `.env`:
```env
# PostgreSQL
DATABASE_URL=postgresql://lumarank:lumarank_password@localhost:5432/lumarank_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=false

# MongoDB
MONGO_URL=mongodb://admin:admin_password@localhost:27017/lumarank?authSource=admin
MONGO_DATABASE=lumarank
MONGO_MAX_POOL_SIZE=100
MONGO_MIN_POOL_SIZE=10
```

## Migrations

### Creating New Migrations

1. Create SQL files:
```bash
# Create upgrade/downgrade SQL files
touch alembic/sql/004_your_migration_upgrade.sql
touch alembic/sql/004_your_migration_downgrade.sql
```

2. Generate migration:
```bash
poetry run alembic revision -m "your_migration_description"
```

3. Update the generated file:
```python
def upgrade() -> None:
    sql = read_sql_file("004_your_migration_upgrade.sql")
    op.execute(sql)

def downgrade() -> None:
    sql = read_sql_file("004_your_migration_downgrade.sql")
    op.execute(sql)
```

## Testing

### Unit Tests
- Models: `tests/unit/test_database_models.py`
- Connection pool: `tests/unit/test_db.py`
- Migrations: `tests/unit/test_migrations.py`

### Integration Tests
Mark tests with `@pytest.mark.integration` and use `test_db_session` fixture:

```python
@pytest.mark.integration
def test_user_creation(test_db_session):
    user = User(email="test@example.com", first_name="Test", last_name="User")
    test_db_session.add(user)
    test_db_session.commit()
    
    assert user.id is not None
```

## Troubleshooting

### Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker-compose -f docker-compose.dev.yml logs postgres

# Test connection
poetry run python -c "from src.db import engine; print(engine.connect())"
```

### Migration Issues
```bash
# Check current version
poetry run alembic current

# Show migration history
poetry run alembic history

# Manually mark migration as complete (if needed)
poetry run alembic stamp <revision>
```

## Production Deployment

1. Use environment variables for `DATABASE_URL`
2. Enable SSL for PostgreSQL connections
3. Use connection pooling settings appropriate for your load
4. Consider read replicas for scaling
5. Set up automated backups
6. Monitor connection pool metrics