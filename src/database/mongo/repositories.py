"""Repository pattern implementation for MongoDB collections."""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from src.database.mongo.connection import get_collection, Collections
from src.database.mongo.models import (
    WebsiteCrawlData,
    WebsiteCrawlDataCreate,
    WebsiteCrawlDataUpdate,
    CrawlStatus,
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common MongoDB operations."""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    @property
    def collection(self) -> Collection:
        """Get MongoDB collection."""
        return get_collection(self.collection_name)
    
    def create_index(self, keys: List[tuple], unique: bool = False, **kwargs):
        """Create index on collection."""
        try:
            return self.collection.create_index(keys, unique=unique, **kwargs)
        except PyMongoError as e:
            logger.error(f"Failed to create index: {e}")
            raise


class WebsiteCrawlDataRepository(BaseRepository):
    """Repository for website crawl data operations."""
    
    def __init__(self):
        super().__init__(Collections.WEBSITE_CRAWL_DATA)
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist."""
        try:
            # Unique index on website_url
            self.create_index([("website_url", 1)], unique=True)
            
            # Index on domain for queries
            self.create_index([("domain", 1)])
            
            # Index on entity_id for filtering
            self.create_index([("entity_id", 1)])
            
            # Index on crawl_status for filtering
            self.create_index([("crawl_status", 1)])
            
            # Compound index for time-based queries
            self.create_index([("created_at", -1), ("crawl_status", 1)])
            
            # Compound index for entity-based queries
            self.create_index([("entity_id", 1), ("created_at", -1)])
            
            # Text index for search
            self.create_index([
                ("company_name", "text"),
                ("page_title", "text"),
                ("meta_description", "text"),
            ])
            
            logger.info(f"Indexes created for {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    def create(self, data: WebsiteCrawlDataCreate) -> WebsiteCrawlData:
        """
        Create new website crawl data.
        
        Args:
            data: Website crawl data to create
            
        Returns:
            Created WebsiteCrawlData with ID
        """
        try:
            # Create document
            doc = WebsiteCrawlData(
                **data.dict(),
                crawl_status=CrawlStatus.PENDING,
                crawl_started_at=datetime.utcnow(),
            )
            
            # Insert into MongoDB
            result = self.collection.insert_one(doc.dict(by_alias=True))
            
            # Return with ID
            doc.id = result.inserted_id
            return doc
            
        except DuplicateKeyError:
            logger.warning(f"Duplicate crawl data for URL: {data.website_url}")
            raise ValueError(f"Crawl data already exists for URL: {data.website_url}")
        except Exception as e:
            logger.error(f"Failed to create crawl data: {e}")
            raise
    
    def get_by_id(self, crawl_id: str) -> Optional[WebsiteCrawlData]:
        """Get crawl data by ID."""
        try:
            doc = self.collection.find_one({"_id": ObjectId(crawl_id)})
            return WebsiteCrawlData(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get crawl data by ID: {e}")
            return None
    
    def get_by_url(self, url: str) -> Optional[WebsiteCrawlData]:
        """Get crawl data by website URL."""
        try:
            doc = self.collection.find_one({"website_url": url})
            return WebsiteCrawlData(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get crawl data by URL: {e}")
            return None
    
    def update(
        self, 
        crawl_id: str, 
        data: WebsiteCrawlDataUpdate
    ) -> Optional[WebsiteCrawlData]:
        """
        Update crawl data.
        
        Args:
            crawl_id: ID of crawl data to update
            data: Update data
            
        Returns:
            Updated WebsiteCrawlData or None if not found
        """
        try:
            # Prepare update data
            update_data = data.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Calculate duration if completed
            if data.crawl_status in [CrawlStatus.COMPLETED, CrawlStatus.FAILED]:
                crawl = self.get_by_id(crawl_id)
                if crawl and crawl.crawl_started_at:
                    duration = datetime.utcnow() - crawl.crawl_started_at
                    update_data["crawl_duration_seconds"] = duration.total_seconds()
                    update_data["crawl_completed_at"] = datetime.utcnow()
            
            # Update document
            result = self.collection.find_one_and_update(
                {"_id": ObjectId(crawl_id)},
                {"$set": update_data},
                return_document=True
            )
            
            return WebsiteCrawlData(**result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to update crawl data: {e}")
            raise
    
    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CrawlStatus] = None,
        domain: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: int = -1,
    ) -> List[WebsiteCrawlData]:
        """
        List crawl data with pagination and filtering.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Filter by crawl status
            domain: Filter by domain
            sort_by: Field to sort by
            sort_order: Sort order (1=asc, -1=desc)
            
        Returns:
            List of WebsiteCrawlData
        """
        try:
            # Build query
            query = {}
            if status:
                query["crawl_status"] = status
            if domain:
                query["domain"] = domain
            
            # Execute query
            cursor = self.collection.find(query).sort(
                sort_by, sort_order
            ).skip(skip).limit(limit)
            
            return [WebsiteCrawlData(**doc) for doc in cursor]
            
        except Exception as e:
            logger.error(f"Failed to list crawl data: {e}")
            return []
    
    def delete(self, crawl_id: str) -> bool:
        """
        Delete crawl data by ID.
        
        Args:
            crawl_id: ID of crawl data to delete
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(crawl_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete crawl data: {e}")
            return False
    
    def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WebsiteCrawlData]:
        """
        Full-text search across crawl data.
        
        Args:
            query: Search query
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of matching WebsiteCrawlData
        """
        try:
            cursor = self.collection.find(
                {"$text": {"$search": query}}
            ).skip(skip).limit(limit)
            
            return [WebsiteCrawlData(**doc) for doc in cursor]
            
        except Exception as e:
            logger.error(f"Failed to search crawl data: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crawl data statistics."""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$crawl_status",
                        "count": {"$sum": 1},
                        "avg_duration": {"$avg": "$crawl_duration_seconds"},
                        "avg_seo_score": {"$avg": "$seo_score"},
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$count"},
                        "by_status": {
                            "$push": {
                                "status": "$_id",
                                "count": "$count",
                                "avg_duration": "$avg_duration",
                                "avg_seo_score": "$avg_seo_score",
                            }
                        }
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop("_id", None)
                return stats
            
            return {"total": 0, "by_status": []}
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}