"""
Website Analyzer Library
Shared library for analyzing websites and generating customer search questions with scoring
"""

import requests
from bs4 import BeautifulSoup
import openai
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from tools import ToolManager, WebSearchTool, NewsTool, TavilyTool

model = "o4-mini"

class WebsiteAnalyzer:
    """
    Main class for website analysis functionality
    """
    
    def __init__(self, api_key: str, serper_api_key: Optional[str] = None, news_api_key: Optional[str] = None, tavily_api_key: Optional[str] = None):
        """
        Initialize the analyzer with OpenAI API key and optional tool API keys
        
        Args:
            api_key: OpenAI API key
            serper_api_key: Optional Serper API key for web search
            news_api_key: Optional NewsAPI key for news search
            tavily_api_key: Optional Tavily API key for AI-optimized search and news
        """
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
        
        # Initialize tool manager and register tools
        self.tool_manager = ToolManager()
        
        # Prefer Tavily over other tools if available
        if tavily_api_key:
            self.tool_manager.register_tool(TavilyTool(tavily_api_key))
        else:
            if serper_api_key:
                self.tool_manager.register_tool(WebSearchTool(serper_api_key))
            
            if news_api_key:
                self.tool_manager.register_tool(NewsTool(news_api_key))
    
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

        Please structure your response as a JSON object with the keys: "company_description", "ideal_customer_profile", "validation_traction", "features", "pricing". ONLY return valid json, do not include any additional text or explanations. The outout must be a valid JSON object with the specified keys. Each key should have at most 2-3 sentences, except for the "company_description" which can be a bit longer.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a business analyst expert at analyzing companies and their offerings. Provide detailed but concise analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Try to parse as JSON, fallback to plain text if it fails
            print("OpenAI response for analysis", response)
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

        1. COMPANY-SPECIFIC QUESTIONS (3 questions that mention the company name "{company_name}"):
           - Include questions about reviews, features, pricing, comparisons
           - Examples: "Are there any reviews of {company_name}?", "What is {company_name}'s feature set and what problems does it solve?", "How does {company_name} compare to other solutions?", "What is the security posture for {company_name}?"

        2. PROBLEM-BASED QUESTIONS (3 questions that don't mention the company at all):
           - Focus on the problems/pain points the company solves
           - What would someone search for when they have the problem this company solves?
           - Think about the keywords and phrases potential customers would use

        Please structure your response as a JSON object with the keys: "company_specific_questions" (array), "problem_based_questions" (array).
        """
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a marketing expert who understands customer search behavior and intent. Generate realistic search queries that potential customers would actually type."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=5000,
                response_format={"type": "json_object"}
            )
            
            print(response)
            try:
                questions = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                questions = {"raw_questions": response.choices[0].message.content}
            
            return questions
            
        except Exception as e:
            raise Exception(f"Error generating questions with OpenAI: {e}")
    
    def query_openai_with_question(self, question: str, is_problem_question: bool) -> Dict[str, Any]:
        """
        Query OpenAI with a fresh context using the provided question, with optional tool calling
        
        Args:
            question: Question to ask OpenAI
            is_problem_question: Whether this is a problem-based question
            
        Returns:
            OpenAI response with answer and score
        """

        extra_problem_text = ""
        if is_problem_question:
            extra_problem_text = "If possible, also suggest the top companies/products that solve the pain point described in the question. Your goal is to help the asker find the best solution to the problem."

        system_prompt = f"""
        You are a helpful assistant that answers questions about companies and products. 
        Today's date is {datetime.now().strftime('%Y-%m-%d')}.
        
        If you need current information that's not in your training data, use the available tools:
        - tavily_search: For AI-optimized web searches, news, and company information (heavily preferred)
        - web_search: For general web searches about companies, products, or topics
        - get_recent_news: For recent news articles about companies or topics
        
        You have two tasks:
        1. Answer the question: {question}
           - Provide a direct response with relevant details
        2. Score your response (0-2) based on helpfulness to a prospective customer
           - 0: Poor quality, not helpful
           - 1: Moderate quality, somewhat helpful  
           - 2: High quality, very helpful
        
        {extra_problem_text}
        
        IMPORTANT: Never make up information. If you don't have enough information, say so.
        Structure your response as JSON with keys: "answer" and "score".
        """

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            # Get tool definitions if tools are available
            tools = self.tool_manager.get_function_definitions() if self.tool_manager.tools else None
            print(tools)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                max_completion_tokens=1500,
                response_format={"type": "json_object"} if not tools else None
            )
            
            print("init response", response)
            # Handle tool calls
            if response.choices[0].message.tool_calls:
                tool_calls = response.choices[0].message.tool_calls
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": tool_calls
                })
                
                # Execute each tool call and add results
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    print("Attempting tool call", function_name, function_args)
                    # Execute the function
                    tool_result = self.tool_manager.execute_tool(function_name, function_args)
                    print("Tool result", tool_result)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                response = final_response
            
            print("OpenAI response", question, response)
            print()
            
            try:
                answer = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                answer = {"raw_answers": response.choices[0].message.content}
            
            return answer
            
        except Exception as e:
            return {"error": f"Error querying OpenAI: {e}", "answer": "", "score": 0}
    
    def score_problem_based_response(self, response: Dict[str, Any], company_name: str) -> int:
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
    
    def test_questions_with_scoring(self, questions: Dict[str, Any], company_name: str) -> Dict[str, Any]:
        """
        Test all generated questions with OpenAI and score the responses using parallel execution
        
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
        
        company_questions = questions.get('company_specific_questions', [])
        problem_questions = questions.get('problem_based_questions', [])
        
        # Use ThreadPoolExecutor to parallelize API calls
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all company-specific questions
            company_futures = [
                executor.submit(self.query_openai_with_question, question, False)
                for question in company_questions
            ]
            
            # Submit all problem-based questions  
            problem_futures = [
                executor.submit(self.query_openai_with_question, question, True)
                for question in problem_questions
            ]
            
            # Process company-specific results
            for i, future in enumerate(company_futures):
                try:
                    response = future.result()
                    answer = response.get("answer", "")
                    score = response.get("score", 0)
                    
                    results["company_specific_results"].append({
                        "question": company_questions[i],
                        "response": answer,
                        "score": score,
                    })
                    results["company_specific_score"] += score
                except Exception as e:
                    print(f"Error processing company question '{company_questions[i]}': {e}")
                    results["company_specific_results"].append({
                        "question": company_questions[i],
                        "response": f"Error: {e}",
                        "score": 0,
                    })
            
            # Process problem-based results
            for i, future in enumerate(problem_futures):
                try:
                    response = future.result()
                    answer = response.get("answer", "")
                    score = self.score_problem_based_response(answer, company_name)
                    
                    results["problem_based_results"].append({
                        "question": problem_questions[i],
                        "response": answer,
                        "score": score,
                    })
                    results["problem_based_score"] += score
                except Exception as e:
                    print(f"Error processing problem question '{problem_questions[i]}': {e}")
                    results["problem_based_results"].append({
                        "question": problem_questions[i],
                        "response": f"Error: {e}",
                        "score": 0,
                    })
        
        print("Company specific results", results["company_specific_results"])
        print("Problem based results", results["problem_based_results"])
        
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
        
        questions["company_specific_questions"] = [f"""What is {company_name}'s feature set and what problems does it solve?""", f"""Are there any reviews or case studies for {company_name}? If so, how did {company_name} help the customer?""", f"""Has {company_name} or {company_name}'s founder been written about in any articles or blogs? If so, which ones and what do they say?"""]
        print("Generated questions", questions)
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
            "scoring_results": scoring_results,
            "suggestions": ["Add an llms.txt file"]
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
