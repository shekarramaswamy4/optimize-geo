import asyncio
import json
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
import openai
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import Settings
from src.core.exceptions import OpenAIError, WebsiteFetchError
from src.models.schemas import (
    CompanyInfo,
    QuestionType,
    SearchQuestion,
    TestResult,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WebsiteAnalyzerService:
    """Service for analyzing websites and generating search questions with scoring."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize the analyzer service."""
        self.settings = settings
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout),
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; WebsiteAnalyzer/1.0)"
            },
        )
    
    async def __aenter__(self) -> "WebsiteAnalyzerService":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the service and cleanup resources."""
        await self.http_client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def fetch_website_content(self, url: str) -> str:
        """Fetch and extract text content from a website."""
        logger.info("Fetching website content", url=str(url))
        
        try:
            response = await self.http_client.get(str(url), follow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            # Limit text length to avoid token limits
            max_chars = 50000
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning("Website content truncated", original_length=len(text))
            
            logger.info("Website content fetched successfully", content_length=len(text))
            return text
            
        except httpx.RequestError as e:
            logger.error("Failed to fetch website", url=str(url), error=str(e))
            raise WebsiteFetchError(str(url), str(e))
        except Exception as e:
            logger.error("Error processing website content", url=str(url), error=str(e))
            raise WebsiteFetchError(str(url), f"Processing error: {e}")
    
    async def analyze_content(self, content: str) -> CompanyInfo:
        """Analyze website content using OpenAI."""
        logger.info("Analyzing website content with OpenAI")
        
        prompt = f"""
        Analyze the following website content and provide a structured analysis:

        Website Content:
        {content[:10000]}  # Limit content to avoid token limits

        Please provide the following information:

        1. Company Name: What is the company name?
        2. Company Description: In 3-4 sentences, what does the company do?
        3. Ideal Customer Profile (ICP): Who is the target customer?
        4. Key Features: What are the main features or services offered?
        5. Pricing: What is the pricing information, if available?
        6. Industry: What industry or sector does the company operate in?

        Respond with a JSON object with the following structure:
        {{
            "name": "Company Name",
            "description": "Company description",
            "ideal_customer_profile": "Target customer description",
            "key_features": ["feature1", "feature2", ...],
            "pricing_info": "Pricing details or null if not available",
            "industry": "Industry/sector"
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business analyst expert. Provide structured JSON responses."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Ensure all required fields have defaults
            company_info = CompanyInfo(
                name=data.get("name", "Unknown Company"),
                description=data.get("description", "No description available"),
                ideal_customer_profile=data.get("ideal_customer_profile", "Not specified"),
                key_features=data.get("key_features", []),
                pricing_info=data.get("pricing_info"),
                industry=data.get("industry"),
            )
            
            logger.info("Content analysis completed", company_name=company_info.name)
            return company_info
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse OpenAI response as JSON", error=str(e))
            raise OpenAIError("Invalid response format from OpenAI")
        except Exception as e:
            logger.error("OpenAI analysis failed", error=str(e))
            raise OpenAIError(str(e))
    
    async def generate_search_questions(
        self, company_info: CompanyInfo
    ) -> dict[str, list[SearchQuestion]]:
        """Generate search questions that prospective customers might ask."""
        logger.info("Generating search questions", company_name=company_info.name)
        
        prompt = f"""
        Based on the following company information, generate search questions that prospective customers might ask:

        Company: {company_info.name}
        Description: {company_info.description}
        Target Customers: {company_info.ideal_customer_profile}
        Key Features: {', '.join(company_info.key_features)}
        Industry: {company_info.industry or 'Not specified'}

        Generate two types of questions:

        1. COMPANY-SPECIFIC QUESTIONS (4-5 questions that mention "{company_info.name}"):
           - Reviews and comparisons
           - Features and capabilities
           - Pricing and plans
           - Security and reliability

        2. PROBLEM-BASED QUESTIONS (5 questions that don't mention the company):
           - Focus on problems the company solves
           - Use keywords customers would search for
           - Consider the customer's pain points

        Respond with a JSON object:
        {{
            "company_specific": [
                {{"question": "...", "intent": "..."}},
                ...
            ],
            "problem_based": [
                {{"question": "...", "intent": "..."}},
                ...
            ]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a marketing expert. Generate realistic search queries."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            data = json.loads(response.choices[0].message.content)
            
            questions: dict[str, list[SearchQuestion]] = {
                "company_specific": [],
                "problem_based": [],
            }
            
            # Parse company-specific questions
            for q in data.get("company_specific", []):
                questions["company_specific"].append(
                    SearchQuestion(
                        question=q["question"],
                        question_type=QuestionType.COMPANY_SPECIFIC,
                        intent=q.get("intent", "Unknown intent"),
                    )
                )
            
            # Parse problem-based questions
            for q in data.get("problem_based", []):
                questions["problem_based"].append(
                    SearchQuestion(
                        question=q["question"],
                        question_type=QuestionType.PROBLEM_BASED,
                        intent=q.get("intent", "Unknown intent"),
                    )
                )
            
            logger.info(
                "Generated search questions",
                company_specific_count=len(questions["company_specific"]),
                problem_based_count=len(questions["problem_based"]),
            )
            
            return questions
            
        except Exception as e:
            logger.error("Failed to generate questions", error=str(e))
            raise OpenAIError(f"Question generation failed: {e}")
    
    async def test_question(
        self, question: SearchQuestion, company_name: str
    ) -> TestResult:
        """Test a single question with OpenAI and score the response."""
        logger.debug("Testing question", question=question.question)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": question.question}],
                max_tokens=500,
                temperature=0.1,
            )
            
            response_text = response.choices[0].message.content
            
            # Score the response based on question type
            if question.question_type == QuestionType.COMPANY_SPECIFIC:
                score, reason = self._score_company_specific_response(
                    response_text, question.question
                )
            else:
                score, reason = self._score_problem_based_response(
                    response_text, company_name
                )
            
            mentions_company = company_name.lower() in response_text.lower()
            
            return TestResult(
                question=question.question,
                question_type=question.question_type,
                response=response_text,
                score=score,
                scoring_reason=reason,
                mentions_company=mentions_company,
            )
            
        except Exception as e:
            logger.error("Failed to test question", question=question.question, error=str(e))
            return TestResult(
                question=question.question,
                question_type=question.question_type,
                response=f"Error: {str(e)}",
                score=0,
                scoring_reason="Failed to get response",
                mentions_company=False,
            )
    
    async def test_all_questions(
        self, questions: dict[str, list[SearchQuestion]], company_name: str
    ) -> tuple[list[TestResult], float]:
        """Test all questions and calculate success rate."""
        logger.info("Testing all generated questions")
        
        all_questions = []
        for question_list in questions.values():
            all_questions.extend(question_list)
        
        # Test questions concurrently
        tasks = [
            self.test_question(question, company_name)
            for question in all_questions
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Calculate success rate
        total_score = sum(result.score for result in results)
        max_score = len(results) * 2  # Max score of 2 per question
        success_rate = total_score / max_score if max_score > 0 else 0.0
        
        logger.info(
            "Question testing completed",
            total_questions=len(results),
            total_score=total_score,
            success_rate=success_rate,
        )
        
        return results, success_rate
    
    def _score_company_specific_response(
        self, response: str, question: str
    ) -> tuple[int, str]:
        """Score company-specific question responses."""
        if not response or "Error" in response:
            return 0, "No valid response"
        
        response_lower = response.lower()
        question_lower = question.lower()
        
        # Check response quality indicators
        quality_indicators = [
            "features", "pricing", "reviews", "comparison", "benefits",
            "customers", "solution", "product", "service", "platform",
        ]
        
        indicator_count = sum(1 for ind in quality_indicators if ind in response_lower)
        
        # Check if response addresses the question
        addresses_question = False
        if "review" in question_lower and any(
            word in response_lower for word in ["review", "rating", "feedback"]
        ):
            addresses_question = True
        elif "feature" in question_lower and any(
            word in response_lower for word in ["feature", "capability", "function"]
        ):
            addresses_question = True
        elif "pric" in question_lower and any(
            word in response_lower for word in ["price", "cost", "fee", "subscription"]
        ):
            addresses_question = True
        
        # Scoring
        if len(response) < 50:
            return 0, "Response too short"
        elif len(response) > 200 and indicator_count >= 3 and addresses_question:
            return 2, "Comprehensive and relevant response"
        elif len(response) > 100 and (indicator_count >= 2 or addresses_question):
            return 1, "Moderately helpful response"
        else:
            return 0, "Response not particularly helpful"
    
    def _score_problem_based_response(
        self, response: str, company_name: str
    ) -> tuple[int, str]:
        """Score problem-based question responses."""
        if not response or "Error" in response:
            return 0, "No valid response"
        
        response_lower = response.lower()
        company_lower = company_name.lower()
        
        if company_lower not in response_lower:
            return 0, f"{company_name} not mentioned"
        
        # Check if company is mentioned first
        words = response.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                if word.lower() == company_lower:
                    return 2, f"{company_name} mentioned first"
                elif any(suffix in word.lower() for suffix in ["inc", "corp", "ltd", "llc"]):
                    return 1, f"{company_name} mentioned but not first"
        
        return 1, f"{company_name} mentioned in response"
    
    def extract_company_name_from_url(self, url: str) -> str:
        """Extract company name from URL."""
        try:
            parsed = urlparse(str(url))
            domain = parsed.netloc.replace("www.", "")
            if not domain:
                return "Company"
            company_name = domain.split(".")[0]
            if not company_name:
                return "Company"
            return company_name.capitalize()
        except Exception:
            return "Company"