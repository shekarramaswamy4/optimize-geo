"""
Website Analyzer Library
Shared library for analyzing websites and generating customer search questions with scoring
"""

import requests
from bs4 import BeautifulSoup
import openai
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class WebsiteAnalyzer:
    """
    Main class for website analysis functionality
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the analyzer with OpenAI API key
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
    
    def fetch_website_content(self, url: str) -> str:
        """
        Fetch and extract text content from a website
        
        Args:
            url: Website URL to fetch
            
        Returns:
            Cleaned text content from the website
            
        Raises:
            Exception: If website cannot be fetched or processed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except requests.RequestException as e:
            raise Exception(f"Error fetching website: {e}")
        except Exception as e:
            raise Exception(f"Error processing website content: {e}")
    
    def analyze_website_content(self, content: str) -> Dict[str, Any]:
        """
        Use OpenAI API to analyze website content
        
        Args:
            content: Website text content to analyze
            
        Returns:
            Dictionary containing analysis results
            
        Raises:
            Exception: If analysis fails
        """
        prompt = f"""
        Analyze the following website content and provide a structured analysis:

        Website Content:
        {content}

        Please provide the following information in a structured format:

        1. Company Description: In 3-4 sentences, what does the company do?
        2. Ideal Customer Profile (ICP): Who is the target customer?
        3. Validation/Traction: What validation or traction does the company have, if any?
        4. Features: What are the listed features of the product/service?
        5. Pricing: What is the pricing for the product, if any can be found?

        Please structure your response as a JSON object with the keys: "company_description", "ideal_customer_profile", "validation_traction", "features", "pricing".
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert at analyzing companies and their offerings. Provide detailed but concise analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            # Try to parse as JSON, fallback to plain text if it fails
            try:
                analysis = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw content
                analysis = {"raw_analysis": response.choices[0].message.content}
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing content with OpenAI: {e}")
    
    def generate_search_questions(self, analysis: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """
        Generate search questions that prospective customers might ask
        
        Args:
            analysis: Company analysis dictionary
            company_name: Name of the company
            
        Returns:
            Dictionary containing generated questions
            
        Raises:
            Exception: If question generation fails
        """
        prompt = f"""
        Based on the following company analysis, generate search questions that prospective customers might ask when looking for solutions like this company provides.

        Company Analysis:
        {json.dumps(analysis, indent=2)}

        Generate two types of questions:

        1. COMPANY-SPECIFIC QUESTIONS (4-5 questions that mention the company name "{company_name}"):
           - Include questions about reviews, features, pricing, comparisons
           - Examples: "Are there any reviews of {company_name}?", "What is {company_name}'s feature set and what problems does it solve?", "How does {company_name} compare to other solutions?", "What is the security posture for {company_name}?"

        2. PROBLEM-BASED QUESTIONS (5 questions that don't mention the company at all):
           - Focus on the problems/pain points the company solves
           - What would someone search for when they have the problem this company solves?
           - Think about the keywords and phrases potential customers would use

        Please structure your response as a JSON object with the keys: "company_specific_questions" (array), "problem_based_questions" (array).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a marketing expert who understands customer search behavior and intent. Generate realistic search queries that potential customers would actually type."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                questions = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                questions = {"raw_questions": response.choices[0].message.content}
            
            return questions
            
        except Exception as e:
            raise Exception(f"Error generating questions with OpenAI: {e}")
    
    def query_openai_with_question(self, question: str) -> str:
        """
        Query OpenAI with a fresh context using the provided question
        
        Args:
            question: Question to ask OpenAI
            
        Returns:
            OpenAI response text
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error querying OpenAI: {e}"
    
    def score_problem_based_response(self, response: str, company_name: str) -> int:
        """
        Score problem-based question responses:
        0 - Company not mentioned at all
        1 - Company mentioned
        2 - Company is the first company mentioned
        
        Args:
            response: OpenAI response to score
            company_name: Name of the company to look for
            
        Returns:
            Score from 0-2
        """
        if not response or "Error" in response:
            return 0
        
        response_lower = response.lower()
        company_lower = company_name.lower()
        
        if company_lower not in response_lower:
            return 0
        
        # Find first company mention (look for patterns like "Company X", "X is", "X offers", etc.)
        words = response.split()
        for i, word in enumerate(words):
            # Check if this word might be a company name (capitalized, not common words)
            if (word[0].isupper() and len(word) > 2 and 
                word not in ['The', 'This', 'That', 'These', 'Those', 'A', 'An', 'And', 'But', 'Or', 'For', 'So', 'Yet']):
                if word.lower() == company_lower:
                    return 2  # First company mentioned
                elif any(common in word.lower() for common in ['inc', 'corp', 'ltd', 'llc', 'co']):
                    return 1  # Another company mentioned first
        
        return 1  # Company mentioned but not first
    
    def score_company_specific_response(self, response: str, question: str) -> int:
        """
        Score company-specific question responses subjectively:
        0 - Poor quality, not helpful
        1 - Moderate quality, somewhat helpful
        2 - High quality, very helpful
        
        Args:
            response: OpenAI response to score
            question: Original question asked
            
        Returns:
            Score from 0-2
        """
        if not response or "Error" in response:
            return 0
        
        # Simple heuristics for response quality
        response_length = len(response)
        
        # Check for informative content
        helpful_indicators = [
            'features', 'pricing', 'reviews', 'comparison', 'benefits', 
            'customers', 'solution', 'product', 'service', 'platform'
        ]
        
        question_lower = question.lower()
        response_lower = response.lower()
        
        # Count relevant keywords
        relevant_keywords = sum(1 for indicator in helpful_indicators if indicator in response_lower)
        
        # Check if response addresses the question
        addresses_question = False
        if 'review' in question_lower and any(word in response_lower for word in ['review', 'rating', 'feedback', 'opinion']):
            addresses_question = True
        elif 'feature' in question_lower and any(word in response_lower for word in ['feature', 'capability', 'function']):
            addresses_question = True
        elif 'pric' in question_lower and any(word in response_lower for word in ['price', 'cost', 'fee', 'subscription']):
            addresses_question = True
        elif 'compar' in question_lower and any(word in response_lower for word in ['compare', 'versus', 'vs', 'alternative']):
            addresses_question = True
        
        # Scoring logic
        if response_length < 50:
            return 0  # Too short to be helpful
        elif response_length > 200 and relevant_keywords >= 3 and addresses_question:
            return 2  # Comprehensive and relevant
        elif response_length > 100 and (relevant_keywords >= 2 or addresses_question):
            return 1  # Moderately helpful
        else:
            return 0  # Not particularly helpful
    
    def test_questions_with_scoring(self, questions: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """
        Test all generated questions with OpenAI and score the responses
        
        Args:
            questions: Dictionary containing generated questions
            company_name: Name of the company
            
        Returns:
            Dictionary containing test results and scores
        """
        results = {
            "company_specific_results": [],
            "problem_based_results": [],
            "company_specific_score": 0,
            "problem_based_score": 0,
            "total_score": 0,
            "max_possible_score": 0
        }
        
        # Test company-specific questions
        company_questions = questions.get('company_specific_questions', [])
        for question in company_questions:
            response = self.query_openai_with_question(question)
            score = self.score_company_specific_response(response, question)
            
            results["company_specific_results"].append({
                "question": question,
                "response": response,
                "score": score,
                "score_explanation": "Poor" if score == 0 else "Moderate" if score == 1 else "High"
            })
            results["company_specific_score"] += score
        
        # Test problem-based questions
        problem_questions = questions.get('problem_based_questions', [])
        for question in problem_questions:
            response = self.query_openai_with_question(question)
            score = self.score_problem_based_response(response, company_name)
            
            mention_status = "Not mentioned" if score == 0 else "Mentioned" if score == 1 else "First mentioned"
            
            results["problem_based_results"].append({
                "question": question,
                "response": response,
                "score": score,
                "score_explanation": f"{company_name} {mention_status}"
            })
            results["problem_based_score"] += score
        
        # Calculate totals
        results["total_score"] = results["company_specific_score"] + results["problem_based_score"]
        results["max_possible_score"] = len(company_questions) * 2 + len(problem_questions) * 2
        
        if results["max_possible_score"] > 0:
            results["success_rate"] = round((results["total_score"] / results["max_possible_score"]) * 100, 1)
        else:
            results["success_rate"] = 0
        
        return results
    
    def analyze_website_complete(self, website_url: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete website analysis workflow
        
        Args:
            website_url: URL of website to analyze
            company_name: Optional company name, will be extracted from URL if not provided
            
        Returns:
            Complete analysis results including scoring
            
        Raises:
            Exception: If any step of the analysis fails
        """
        # Extract company name from URL if not provided
        if not company_name:
            company_name = self.extract_company_name_from_url(website_url)
        
        # Fetch website content
        content = self.fetch_website_content(website_url)
        
        # Analyze content
        analysis = self.analyze_website_content(content)
        
        # Generate questions
        questions = self.generate_search_questions(analysis, company_name)
        
        # Test questions and score responses
        if "raw_questions" not in questions:
            scoring_results = self.test_questions_with_scoring(questions, company_name)
        else:
            scoring_results = {"error": "Could not parse generated questions"}
        
        return {
            "website_url": website_url,
            "company_name": company_name,
            "analysis": analysis,
            "questions": questions,
            "scoring_results": scoring_results
        }
    
    @staticmethod
    def extract_company_name_from_url(url: str) -> str:
        """
        Extract company name from URL
        
        Args:
            url: Website URL
            
        Returns:
            Extracted company name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            company_name = domain.split('.')[0]
            return company_name.capitalize()
        except:
            return "Company"


# Utility functions for backwards compatibility
def create_analyzer(api_key: str) -> WebsiteAnalyzer:
    """
    Create a WebsiteAnalyzer instance
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        WebsiteAnalyzer instance
    """
    return WebsiteAnalyzer(api_key)