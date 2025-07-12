"""MongoDB document models using Pydantic for validation."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic models."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        """Update schema for JSON serialization."""
        schema.update(type="string")
        return schema


class CrawlStatus(str, Enum):
    """Status of website crawl."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class WebsiteCrawlData(BaseModel):
    """Website crawl data document model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Website information
    website_url: HttpUrl = Field(..., description="The website URL that was crawled")
    domain: Optional[str] = Field(None, description="Domain name extracted from URL")
    company_name: Optional[str] = Field(None, description="Company name extracted or provided")
    
    # Crawl metadata
    crawl_status: CrawlStatus = Field(default=CrawlStatus.PENDING)
    crawl_started_at: Optional[datetime] = None
    crawl_completed_at: Optional[datetime] = None
    crawl_duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    
    # Extracted content
    raw_html: Optional[str] = Field(None, description="Raw HTML content")
    cleaned_text: Optional[str] = Field(None, description="Cleaned text content")
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    
    # Analysis results (from OpenAI)
    company_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Extracted company information"
    )
    generated_questions: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None,
        description="Generated SEO questions"
    )
    test_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Question test results"
    )
    seo_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall SEO score (0-1)"
    )
    
    # Technical details
    response_headers: Optional[Dict[str, str]] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    entity_id: Optional[str] = Field(None, description="Entity ID this crawl belongs to")
    request_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "website_url": "https://example.com",
                "domain": "example.com",
                "company_name": "Example Corp",
                "crawl_status": "completed",
                "page_title": "Example Corp - Home",
                "seo_score": 0.85,
            }
        }
    
    @validator("domain", pre=True, always=True)
    def extract_domain(cls, v, values):
        """Extract domain from URL if not provided."""
        if v:
            return v
        if "website_url" in values:
            from urllib.parse import urlparse
            parsed = urlparse(str(values["website_url"]))
            return parsed.netloc
        return None
    
    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        """Always update the updated_at timestamp."""
        return datetime.utcnow()
    
    def dict(self, *args, **kwargs):
        """Override dict to handle MongoDB ID field."""
        if "_id" in kwargs.get("exclude", set()):
            kwargs["exclude"].remove("_id")
            kwargs["exclude"] = kwargs.get("exclude", set()) | {"id"}
        return super().dict(*args, **kwargs)


class WebsiteCrawlDataInDB(WebsiteCrawlData):
    """Website crawl data as stored in database."""
    pass


class WebsiteCrawlDataCreate(BaseModel):
    """Schema for creating new crawl data."""
    website_url: HttpUrl
    company_name: Optional[str] = None
    created_by: Optional[str] = None
    entity_id: Optional[str] = None
    request_id: Optional[str] = None


class WebsiteCrawlDataUpdate(BaseModel):
    """Schema for updating crawl data."""
    crawl_status: Optional[CrawlStatus] = None
    error_message: Optional[str] = None
    raw_html: Optional[str] = None
    cleaned_text: Optional[str] = None
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    company_info: Optional[Dict[str, Any]] = None
    generated_questions: Optional[Dict[str, List[Dict[str, Any]]]] = None
    test_results: Optional[List[Dict[str, Any]]] = None
    seo_score: Optional[float] = None
    response_headers: Optional[Dict[str, str]] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None