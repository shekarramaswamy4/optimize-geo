#!/usr/bin/env python3
"""
Website Analyzer Script
Fetches content from spacetil.com and uses OpenAI API to analyze it
"""

import requests
from bs4 import BeautifulSoup
import openai
import os
import sys
from typing import Dict, Any
import json

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
        print(f"Error fetching website: {e}")
        return ""
    except Exception as e:
        print(f"Error processing website content: {e}")
        return ""

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
        print(f"Error analyzing content with OpenAI: {e}")
        return {"error": str(e)}

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
        print(f"Error generating questions with OpenAI: {e}")
        return {"error": str(e)}

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
    
    print("\nTesting questions with OpenAI and scoring responses...")
    
    # Test company-specific questions
    company_questions = questions.get('company_specific_questions', [])
    for i, question in enumerate(company_questions, 1):
        print(f"Testing company question {i}/{len(company_questions)}: {question[:60]}...")
        response = query_openai_with_question(question, api_key)
        score = score_company_specific_response(response, question)
        
        results["company_specific_results"].append({
            "question": question,
            "response": response,
            "score": score
        })
        results["company_specific_score"] += score
    
    # Test problem-based questions
    problem_questions = questions.get('problem_based_questions', [])
    for i, question in enumerate(problem_questions, 1):
        print(f"Testing problem question {i}/{len(problem_questions)}: {question[:60]}...")
        response = query_openai_with_question(question, api_key)
        score = score_problem_based_response(response, company_name)
        
        results["problem_based_results"].append({
            "question": question,
            "response": response,
            "score": score
        })
        results["problem_based_score"] += score
    
    # Calculate totals
    results["total_score"] = results["company_specific_score"] + results["problem_based_score"]
    results["max_possible_score"] = len(company_questions) * 2 + len(problem_questions) * 2
    
    return results

def main():
    """
    Main function to run the website analyzer
    """
    website_url = "https://spacetil.com"
    company_name = "SpaceTil"
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: Please set your OPENAI_API_KEY environment variable")
        print("You can set it by running: export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    print(f"Fetching content from {website_url}...")
    content = fetch_website_content(website_url)
    
    if not content:
        print("Failed to fetch website content")
        sys.exit(1)
    
    print(f"Successfully fetched {len(content)} characters of content")
    print("\nAnalyzing content with OpenAI...")
    
    analysis = analyze_website_content(content, api_key)
    
    if "error" in analysis:
        print(f"Analysis failed: {analysis['error']}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("SPACETIL.COM ANALYSIS RESULTS")
    print("="*60)
    
    if "raw_analysis" in analysis:
        print(analysis["raw_analysis"])
    else:
        print(f"\n1. COMPANY DESCRIPTION:")
        print(f"   {analysis.get('company_description', 'Not found')}")
        
        print(f"\n2. IDEAL CUSTOMER PROFILE (ICP):")
        print(f"   {analysis.get('ideal_customer_profile', 'Not found')}")
        
        print(f"\n3. VALIDATION/TRACTION:")
        print(f"   {analysis.get('validation_traction', 'Not found')}")
        
        print(f"\n4. FEATURES:")
        features = analysis.get('features', 'Not found')
        if isinstance(features, list):
            for feature in features:
                print(f"   - {feature}")
        else:
            print(f"   {features}")
        
        print(f"\n5. PRICING:")
        print(f"   {analysis.get('pricing', 'Not found')}")
    
    print("\n" + "="*60)
    
    # Generate search questions
    print("\nGenerating customer search questions...")
    questions = generate_search_questions(analysis, api_key, company_name)
    
    if "error" in questions:
        print(f"Question generation failed: {questions['error']}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("CUSTOMER SEARCH QUESTIONS")
    print("="*60)
    
    if "raw_questions" in questions:
        print(questions["raw_questions"])
    else:
        print(f"\nCOMPANY-SPECIFIC QUESTIONS:")
        print(f"(Questions mentioning '{company_name}')")
        company_questions = questions.get('company_specific_questions', [])
        for i, question in enumerate(company_questions, 1):
            print(f"   {i}. {question}")
        
        print(f"\nPROBLEM-BASED QUESTIONS:")
        print(f"(Questions about solutions without mentioning the company)")
        problem_questions = questions.get('problem_based_questions', [])
        for i, question in enumerate(problem_questions, 1):
            print(f"   {i}. {question}")
    
    print("\n" + "="*60)
    
    # Test questions and score responses
    if "raw_questions" not in questions:
        scoring_results = test_questions_with_scoring(questions, api_key, company_name)
        
        print("\n" + "="*60)
        print("QUESTION TESTING & SCORING RESULTS")
        print("="*60)
        
        # Display company-specific results
        print(f"\nCOMPANY-SPECIFIC QUESTION RESULTS:")
        for i, result in enumerate(scoring_results["company_specific_results"], 1):
            print(f"\n   Q{i}: {result['question']}")
            print(f"   Response: {result['response']}")
            print(f"   Score: {result['score']}/2 (Quality: {'Poor' if result['score'] == 0 else 'Moderate' if result['score'] == 1 else 'High'})")
        
        # Display problem-based results
        print(f"\nPROBLEM-BASED QUESTION RESULTS:")
        for i, result in enumerate(scoring_results["problem_based_results"], 1):
            print(f"\n   Q{i}: {result['question']}")
            print(f"   Response: {result['response']}")
            mention_status = "Not mentioned" if result['score'] == 0 else "Mentioned" if result['score'] == 1 else "First mentioned"
            print(f"   Score: {result['score']}/2 ({company_name} {mention_status})")
        
        # Display final scores
        print(f"\n" + "="*60)
        print("FINAL SCORING SUMMARY")
        print("="*60)
        print(f"Company-Specific Questions Score: {scoring_results['company_specific_score']}/{len(company_questions) * 2}")
        print(f"Problem-Based Questions Score: {scoring_results['problem_based_score']}/{len(problem_questions) * 2}")
        print(f"TOTAL SCORE: {scoring_results['total_score']}/{scoring_results['max_possible_score']}")
        
        if scoring_results['max_possible_score'] > 0:
            percentage = (scoring_results['total_score'] / scoring_results['max_possible_score']) * 100
            print(f"SUCCESS RATE: {percentage:.1f}%")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
