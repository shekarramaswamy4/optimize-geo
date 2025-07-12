from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_session_context, require_session
from src.api.dependencies import get_analyzer_service, get_request_id
from src.core.auth import SessionContext
from src.core.exceptions import WebsiteAnalyzerError
from src.database import WebsiteCrawlDataRepository, WebsiteCrawlDataCreate, CrawlStatus
from src.models.schemas import (
    AnalysisResponse,
    AnalysisStatus,
    AnalyzeRequest,
    TestQuestionsRequest,
)
from src.services.analyzer import WebsiteAnalyzerService
from src.utils.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["analyzer"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_website(
    request: AnalyzeRequest,
    analyzer: Annotated[WebsiteAnalyzerService, Depends(get_analyzer_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    session: Annotated[SessionContext, Depends(get_session_context)],
) -> AnalysisResponse:
    """
    Analyze a website and generate search questions with optional testing.
    
    This endpoint:
    1. Fetches the website content
    2. Analyzes it to extract company information
    3. Generates search questions
    4. Optionally tests the questions and scores responses
    """
    logger.info(
        "Starting website analysis", 
        url=str(request.website_url),
        user_id=str(session.user.id),
        user_email=session.user.email,
        entity_id=str(session.entity.id),
        entity_name=session.entity.name,
    )
    
    # Create crawl data record in MongoDB
    crawl_repo = WebsiteCrawlDataRepository()
    crawl_data = crawl_repo.create(WebsiteCrawlDataCreate(
        website_url=str(request.website_url),
        company_name=request.company_name,
        created_by=str(session.user.id),
        entity_id=str(session.entity.id),
        request_id=request_id,
    ))
    
    try:
        # Fetch website content
        content = await analyzer.fetch_website_content(request.website_url)
        
        # Analyze content
        company_info = await analyzer.analyze_content(content)
        
        # Override company name if provided
        if request.company_name:
            company_info.name = request.company_name
        
        # Generate questions
        questions = await analyzer.generate_search_questions(company_info)
        
        # Test questions if requested
        test_results = None
        success_rate = None
        
        if request.test_questions:
            test_results, success_rate = await analyzer.test_all_questions(
                questions, company_info.name
            )
        
        return AnalysisResponse(
            request_id=request_id,
            status=AnalysisStatus.COMPLETED,
            company_info=company_info,
            questions=questions,
            test_results=test_results,
            success_rate=success_rate,
            metadata={
                "website_url": str(request.website_url),
                "questions_tested": request.test_questions,
            },
        )
        
    except WebsiteAnalyzerError as e:
        logger.error("Analysis failed", error=str(e), error_code=e.error_code)
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error_code": e.error_code,
                "message": e.message,
                "details": e.details,
            },
        )
    except Exception as e:
        logger.error("Unexpected error during analysis", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )


@router.post("/analyze/quick", response_model=AnalysisResponse, dependencies=[Depends(require_session)])
async def quick_analyze(
    request: AnalyzeRequest,
    analyzer: Annotated[WebsiteAnalyzerService, Depends(get_analyzer_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    session: Annotated[SessionContext, Depends(get_session_context)],
) -> AnalysisResponse:
    """
    Quick analysis without testing the generated questions.
    
    This is faster than the full analysis as it skips the question testing phase.
    """
    # Force test_questions to False for quick analysis
    request.test_questions = False
    return await analyze_website(request, analyzer, request_id, session)


@router.post("/test-questions", response_model=AnalysisResponse, dependencies=[Depends(require_session)])
async def test_questions(
    request: TestQuestionsRequest,
    analyzer: Annotated[WebsiteAnalyzerService, Depends(get_analyzer_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    session: Annotated[SessionContext, Depends(get_session_context)],
) -> AnalysisResponse:
    """
    Test pre-generated questions without analyzing a website.
    
    Useful for testing custom questions or re-testing with different parameters.
    """
    logger.info(
        "Testing pre-generated questions",
        company_name=request.company_name,
        question_count=len(request.questions),
        user_id=str(session.user.id),
        user_email=session.user.email,
        entity_id=str(session.entity.id),
        entity_name=session.entity.name,
    )
    
    try:
        # Group questions by type
        questions = {
            "company_specific": [
                q for q in request.questions
                if q.question_type == "company_specific"
            ],
            "problem_based": [
                q for q in request.questions
                if q.question_type == "problem_based"
            ],
        }
        
        # Test all questions
        test_results, success_rate = await analyzer.test_all_questions(
            questions, request.company_name
        )
        
        # Create a minimal company info for the response
        company_info = {
            "name": request.company_name,
            "description": "Pre-generated questions test",
            "ideal_customer_profile": "N/A",
            "key_features": [],
        }
        
        return AnalysisResponse(
            request_id=request_id,
            status=AnalysisStatus.COMPLETED,
            company_info=company_info,
            questions=questions,
            test_results=test_results,
            success_rate=success_rate,
            metadata={
                "test_only": True,
                "question_count": len(request.questions),
            },
        )
        
    except Exception as e:
        logger.error("Error testing questions", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "TEST_ERROR",
                "message": f"Failed to test questions: {str(e)}",
            },
        )