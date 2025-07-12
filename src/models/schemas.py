from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if request failed")


class QuestionType(str, Enum):
    """Types of search questions."""
    COMPANY_SPECIFIC = "company_specific"
    PROBLEM_BASED = "problem_based"


class AnalysisStatus(str, Enum):
    """Status of analysis tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CompanyInfo(BaseModel):
    """Company information extracted from website."""
    name: str = Field(..., description="Company name")
    description: str = Field(..., description="Company description")
    ideal_customer_profile: str = Field(..., description="Ideal customer profile")
    key_features: list[str] = Field(default_factory=list, description="Key features or services")
    pricing_info: Optional[str] = Field(None, description="Pricing information if available")
    industry: Optional[str] = Field(None, description="Industry or sector")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "TechCorp",
                "description": "Leading provider of cloud solutions",
                "ideal_customer_profile": "Mid-size to enterprise companies",
                "key_features": ["Cloud storage", "Data analytics", "API integration"],
                "pricing_info": "Starting at $99/month",
                "industry": "Technology"
            }
        }


class SearchQuestion(BaseModel):
    """Search question generated for analysis."""
    question: str = Field(..., description="The search question")
    question_type: QuestionType = Field(..., description="Type of question")
    intent: str = Field(..., description="Intent behind the question")
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class TestResult(BaseModel):
    """Result of testing a search question."""
    question: str = Field(..., description="The tested question")
    question_type: QuestionType = Field(..., description="Type of question")
    response: str = Field(..., description="AI response to the question")
    score: int = Field(..., ge=0, le=2, description="Score (0-2)")
    scoring_reason: str = Field(..., description="Reason for the score")
    mentions_company: bool = Field(..., description="Whether response mentions the company")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the best cloud storage solution?",
                "question_type": "problem_based",
                "response": "When it comes to cloud storage...",
                "score": 2,
                "scoring_reason": "Company mentioned prominently",
                "mentions_company": True
            }
        }


class AnalyzeRequest(BaseModel):
    """Request model for website analysis."""
    website_url: HttpUrl = Field(..., description="URL of the website to analyze")
    company_name: Optional[str] = Field(None, description="Company name (optional override)")
    test_questions: bool = Field(True, description="Whether to test generated questions")
    
    @field_validator("website_url")
    @classmethod
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "website_url": "https://example.com",
                "company_name": "Example Corp",
                "test_questions": True
            }
        }


class TestQuestionsRequest(BaseModel):
    """Request model for testing pre-generated questions."""
    company_name: str = Field(..., description="Company name")
    questions: list[SearchQuestion] = Field(..., description="Questions to test")
    
    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[SearchQuestion]) -> list[SearchQuestion]:
        if not v:
            raise ValueError("At least one question must be provided")
        return v


class AnalysisResponse(BaseModel):
    """Response model for website analysis."""
    request_id: str = Field(..., description="Unique request identifier")
    status: AnalysisStatus = Field(..., description="Analysis status")
    company_info: CompanyInfo = Field(..., description="Extracted company information")
    questions: dict[str, list[SearchQuestion]] = Field(
        ...,
        description="Generated questions by type"
    )
    test_results: Optional[list[TestResult]] = Field(
        None,
        description="Test results if questions were tested"
    )
    success_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Success rate of tested questions"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "req_123456",
                "status": "completed",
                "company_info": {
                    "name": "TechCorp",
                    "description": "Leading cloud provider",
                    "ideal_customer_profile": "Enterprise companies",
                    "key_features": ["Storage", "Analytics"],
                    "pricing_info": "$99/month"
                },
                "questions": {
                    "company_specific": [
                        {
                            "question": "What does TechCorp offer?",
                            "question_type": "company_specific",
                            "intent": "Learn about company"
                        }
                    ],
                    "problem_based": [
                        {
                            "question": "Best cloud storage solution?",
                            "question_type": "problem_based",
                            "intent": "Find solution"
                        }
                    ]
                },
                "test_results": [
                    {
                        "question": "What does TechCorp offer?",
                        "question_type": "company_specific",
                        "response": "TechCorp offers...",
                        "score": 2,
                        "scoring_reason": "Comprehensive answer",
                        "mentions_company": True
                    }
                ],
                "success_rate": 0.85,
                "metadata": {"processing_time": 12.5},
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] = Field(default_factory=dict, description="Error details")
    request_id: Optional[str] = Field(None, description="Request ID if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid URL format",
                "details": {"field": "website_url", "value": "not-a-url"},
                "request_id": "req_123456",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = Field(..., description="Environment")
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2024-01-01T00:00:00Z",
                "environment": "production",
                "services": {
                    "openai": "healthy",
                    "database": "healthy"
                }
            }
        }