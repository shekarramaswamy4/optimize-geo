#!/usr/bin/env python3
"""
Website Analyzer Web Server
Flask API that analyzes websites and generates customer search questions with scoring
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import openai
import os
import json
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

def fetch_website_content(url: str) -> str:
    """
    Fetch and extract text content from a website
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

def analyze_website_content(content: str, api_key: str) -> Dict[str, Any]:
    """
    Use OpenAI API to analyze website content
    """
    client = openai.OpenAI(api_key=api_key)
    
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
        response = client.chat.completions.create(
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

def generate_search_questions(analysis: Dict[str, Any], api_key: str, company_name: str) -> Dict[str, Any]:
    """
    Generate search questions that prospective customers might ask
    """
    client = openai.OpenAI(api_key=api_key)
    
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
        response = client.chat.completions.create(
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

def query_openai_with_question(question: str, api_key: str) -> str:
    """
    Query OpenAI with a fresh context using the provided question
    """
    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
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

def score_problem_based_response(response: str, company_name: str) -> int:
    """
    Score problem-based question responses:
    0 - Company not mentioned at all
    1 - Company mentioned
    2 - Company is the first company mentioned
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

def score_company_specific_response(response: str, question: str) -> int:
    """
    Score company-specific question responses subjectively:
    0 - Poor quality, not helpful
    1 - Moderate quality, somewhat helpful
    2 - High quality, very helpful
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

def test_questions_with_scoring(questions: Dict[str, Any], api_key: str, company_name: str) -> Dict[str, Any]:
    """
    Test all generated questions with OpenAI and score the responses
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
        response = query_openai_with_question(question, api_key)
        score = score_company_specific_response(response, question)
        
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
        response = query_openai_with_question(question, api_key)
        score = score_problem_based_response(response, company_name)
        
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

def extract_company_name_from_url(url: str) -> str:
    """
    Extract company name from URL
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        company_name = domain.split('.')[0]
        return company_name.capitalize()
    except:
        return "Company"

@app.route('/analyze', methods=['POST'])
def analyze_website():
    """
    Main API endpoint to analyze a website
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'website_url' not in data:
            return jsonify({"error": "Missing 'website_url' in request body"}), 400
        
        website_url = data['website_url']
        
        # Validate URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({"error": "OpenAI API key not configured"}), 500
        
        # Extract company name from URL
        company_name = extract_company_name_from_url(website_url)
        
        # Fetch website content
        try:
            content = fetch_website_content(website_url)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        # Analyze content
        try:
            analysis = analyze_website_content(content, api_key)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        # Generate questions
        try:
            questions = generate_search_questions(analysis, api_key, company_name)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        # Test questions and score responses
        if "raw_questions" not in questions:
            try:
                scoring_results = test_questions_with_scoring(questions, api_key, company_name)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            scoring_results = {"error": "Could not parse generated questions"}
        
        # Prepare response
        response_data = {
            "website_url": website_url,
            "company_name": company_name,
            "analysis": analysis,
            "questions": questions,
            "scoring_results": scoring_results,
            "success": True
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "success": False}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "message": "Website Analyzer API is running"})

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API documentation
    """
    return jsonify({
        "message": "Website Analyzer API",
        "endpoints": {
            "POST /analyze": {
                "description": "Analyze a website and generate customer search questions with scoring",
                "body": {
                    "website_url": "string (required) - URL of the website to analyze"
                },
                "example": {
                    "website_url": "https://example.com"
                }
            },
            "GET /health": {
                "description": "Health check endpoint"
            }
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)