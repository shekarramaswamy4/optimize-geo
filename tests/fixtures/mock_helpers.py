"""Helper functions for creating test mocks."""

from unittest.mock import AsyncMock, MagicMock

from src.models.schemas import CompanyInfo, QuestionType, SearchQuestion, TestResult
from tests.fixtures.test_data import SAMPLE_COMPANY_ANALYSIS, SAMPLE_QUESTIONS


def create_mock_analyzer_service():
    """Create a fully mocked analyzer service."""
    mock_service = AsyncMock()
    
    # Mock methods
    mock_service.fetch_website_content = AsyncMock(return_value="Website content")
    mock_service.analyze_content = AsyncMock(
        return_value=CompanyInfo(**SAMPLE_COMPANY_ANALYSIS)
    )
    
    # Create search questions
    questions = {
        "company_specific": [
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.COMPANY_SPECIFIC,
                intent=q["intent"]
            ) for q in SAMPLE_QUESTIONS["company_specific"]
        ],
        "problem_based": [
            SearchQuestion(
                question=q["question"],
                question_type=QuestionType.PROBLEM_BASED,
                intent=q["intent"]
            ) for q in SAMPLE_QUESTIONS["problem_based"]
        ],
    }
    mock_service.generate_search_questions = AsyncMock(return_value=questions)
    
    # Create test results
    test_results = [
        TestResult(
            question="Test question",
            question_type=QuestionType.COMPANY_SPECIFIC,
            response="Test response",
            score=2,
            scoring_reason="Good response",
            mentions_company=True
        )
    ]
    mock_service.test_all_questions = AsyncMock(return_value=(test_results, 0.85))
    
    # Mock other methods
    mock_service.test_question = AsyncMock(return_value=test_results[0])
    mock_service.extract_company_name_from_url = MagicMock(return_value="Company")
    mock_service._score_company_specific_response = MagicMock(return_value=(2, "Good"))
    mock_service._score_problem_based_response = MagicMock(return_value=(1, "Mentioned"))
    
    # Mock close method
    mock_service.close = AsyncMock()
    
    return mock_service