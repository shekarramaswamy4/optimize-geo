"""Unit tests for MongoDB models."""

import pytest
from datetime import datetime
from bson import ObjectId
from pydantic import ValidationError

from src.database.mongo.models import (
    PyObjectId,
    CrawlStatus,
    WebsiteCrawlData,
    WebsiteCrawlDataCreate,
    WebsiteCrawlDataUpdate,
)


class TestPyObjectId:
    """Test custom PyObjectId field."""
    
    def test_valid_object_id(self):
        """Test validation of valid ObjectId."""
        valid_id = ObjectId()
        result = PyObjectId.validate(str(valid_id))
        assert isinstance(result, ObjectId)
        assert result == valid_id
    
    def test_invalid_object_id(self):
        """Test validation of invalid ObjectId."""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")
    
    def test_object_id_from_string(self):
        """Test creating ObjectId from string."""
        id_str = "507f1f77bcf86cd799439011"
        result = PyObjectId.validate(id_str)
        assert isinstance(result, ObjectId)
        assert str(result) == id_str


class TestCrawlStatus:
    """Test CrawlStatus enum."""
    
    def test_crawl_status_values(self):
        """Test all crawl status values."""
        assert CrawlStatus.PENDING == "pending"
        assert CrawlStatus.IN_PROGRESS == "in_progress"
        assert CrawlStatus.COMPLETED == "completed"
        assert CrawlStatus.FAILED == "failed"
        assert CrawlStatus.PARTIAL == "partial"


class TestWebsiteCrawlData:
    """Test WebsiteCrawlData model."""
    
    def test_minimal_crawl_data(self):
        """Test creating crawl data with minimal fields."""
        data = WebsiteCrawlData(
            website_url="https://example.com",
        )
        
        assert str(data.website_url) == "https://example.com/"
        assert data.domain == "example.com"
        assert data.crawl_status == CrawlStatus.PENDING
        assert isinstance(data.id, ObjectId)
        assert isinstance(data.created_at, datetime)
        assert isinstance(data.updated_at, datetime)
    
    def test_full_crawl_data(self):
        """Test creating crawl data with all fields."""
        now = datetime.utcnow()
        data = WebsiteCrawlData(
            website_url="https://example.com",
            domain="example.com",
            company_name="Example Corp",
            crawl_status=CrawlStatus.COMPLETED,
            crawl_started_at=now,
            crawl_completed_at=now,
            crawl_duration_seconds=5.5,
            raw_html="<html>...</html>",
            cleaned_text="Example content",
            page_title="Example Page",
            meta_description="Example description",
            meta_keywords=["example", "test"],
            company_info={"name": "Example Corp"},
            generated_questions={"company_specific": []},
            test_results=[{"question": "test", "score": 1}],
            seo_score=0.85,
            response_headers={"content-type": "text/html"},
            status_code=200,
            content_type="text/html",
            content_length=1024,
            created_by="user123",
            request_id="req123",
        )
        
        assert data.company_name == "Example Corp"
        assert data.crawl_status == CrawlStatus.COMPLETED
        assert data.seo_score == 0.85
        assert data.status_code == 200
    
    def test_domain_extraction(self):
        """Test automatic domain extraction from URL."""
        data = WebsiteCrawlData(
            website_url="https://subdomain.example.com/page?query=1",
        )
        
        assert data.domain == "subdomain.example.com"
    
    def test_updated_at_always_updates(self):
        """Test that updated_at is always set to current time."""
        data = WebsiteCrawlData(
            website_url="https://example.com",
            updated_at=datetime(2020, 1, 1),
        )
        
        # updated_at should be recent, not the provided old date
        assert data.updated_at > datetime(2020, 1, 1)
        assert (datetime.utcnow() - data.updated_at).total_seconds() < 1
    
    def test_seo_score_validation(self):
        """Test SEO score validation (0-1 range)."""
        # Valid score
        data = WebsiteCrawlData(
            website_url="https://example.com",
            seo_score=0.5,
        )
        assert data.seo_score == 0.5
        
        # Invalid score (too high)
        with pytest.raises(ValidationError):
            WebsiteCrawlData(
                website_url="https://example.com",
                seo_score=1.5,
            )
        
        # Invalid score (negative)
        with pytest.raises(ValidationError):
            WebsiteCrawlData(
                website_url="https://example.com",
                seo_score=-0.1,
            )
    
    def test_json_encoding(self):
        """Test JSON encoding of model."""
        data = WebsiteCrawlData(
            website_url="https://example.com",
        )
        
        json_data = data.json()
        assert isinstance(json_data, str)
        assert "example.com" in json_data
        
        # Check that ObjectId is properly encoded
        # The dict method returns the actual ObjectId, not a string
        dict_data = data.dict(by_alias=True)
        assert isinstance(dict_data["_id"], ObjectId)
        
        # But when serialized to JSON, it should be a string
        import json
        parsed = json.loads(json_data)
        assert isinstance(parsed["id"], str)
    
    def test_dict_method_exclude_id(self):
        """Test dict method with ID exclusion."""
        data = WebsiteCrawlData(
            website_url="https://example.com",
        )
        
        # Test excluding _id field
        dict_data = data.dict(exclude={"_id"})
        assert "id" not in dict_data  # id should be excluded when _id is excluded


class TestWebsiteCrawlDataCreate:
    """Test WebsiteCrawlDataCreate schema."""
    
    def test_create_minimal(self):
        """Test creating with minimal fields."""
        data = WebsiteCrawlDataCreate(
            website_url="https://example.com",
        )
        
        assert str(data.website_url) == "https://example.com/"
        assert data.company_name is None
        assert data.created_by is None
        assert data.request_id is None
    
    def test_create_with_all_fields(self):
        """Test creating with all fields."""
        data = WebsiteCrawlDataCreate(
            website_url="https://example.com",
            company_name="Example Corp",
            created_by="user123",
            request_id="req123",
        )
        
        assert data.company_name == "Example Corp"
        assert data.created_by == "user123"
        assert data.request_id == "req123"


class TestWebsiteCrawlDataUpdate:
    """Test WebsiteCrawlDataUpdate schema."""
    
    def test_update_partial(self):
        """Test partial update."""
        data = WebsiteCrawlDataUpdate(
            crawl_status=CrawlStatus.COMPLETED,
            seo_score=0.9,
        )
        
        update_dict = data.dict(exclude_unset=True)
        assert len(update_dict) == 2
        assert update_dict["crawl_status"] == "completed"
        assert update_dict["seo_score"] == 0.9
    
    def test_update_all_fields(self):
        """Test update with all fields."""
        data = WebsiteCrawlDataUpdate(
            crawl_status=CrawlStatus.COMPLETED,
            error_message=None,
            raw_html="<html>...</html>",
            cleaned_text="Content",
            page_title="Title",
            meta_description="Description",
            meta_keywords=["keyword"],
            company_info={"name": "Company"},
            generated_questions={"company_specific": []},
            test_results=[],
            seo_score=0.8,
            response_headers={"content-type": "text/html"},
            status_code=200,
            content_type="text/html",
            content_length=1024,
        )
        
        update_dict = data.dict(exclude_unset=True)
        assert update_dict["crawl_status"] == "completed"
        assert update_dict["status_code"] == 200
        assert update_dict["seo_score"] == 0.8