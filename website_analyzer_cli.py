#!/usr/bin/env python3
"""
Website Analyzer CLI Script
Command-line interface for website analysis using the shared library
"""

import os
import sys
from website_analyzer_lib import WebsiteAnalyzer


def print_analysis_results(results: dict, verbose: bool = True):
    """
    Print analysis results in a formatted way
    
    Args:
        results: Analysis results dictionary
        verbose: Whether to print detailed results
    """
    website_url = results.get("website_url", "Unknown")
    company_name = results.get("company_name", "Unknown")
    analysis = results.get("analysis", {})
    questions = results.get("questions", {})
    scoring_results = results.get("scoring_results", {})
    
    print("\n" + "="*60)
    print(f"{company_name.upper()} ANALYSIS RESULTS")
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
    
    # Print scoring results if available and verbose mode is on
    if verbose and "error" not in scoring_results and "raw_questions" not in questions:
        print("\n" + "="*60)
        print("QUESTION TESTING & SCORING RESULTS")
        print("="*60)
        
        # Display company-specific results
        print(f"\nCOMPANY-SPECIFIC QUESTION RESULTS:")
        for i, result in enumerate(scoring_results.get("company_specific_results", []), 1):
            print(f"\n   Q{i}: {result['question']}")
            print(f"   Response: {result['response']}")
            print(f"   Score: {result['score']}/2 (Quality: {result['score_explanation']})")
        
        # Display problem-based results
        print(f"\nPROBLEM-BASED QUESTION RESULTS:")
        for i, result in enumerate(scoring_results.get("problem_based_results", []), 1):
            print(f"\n   Q{i}: {result['question']}")
            print(f"   Response: {result['response']}")
            print(f"   Score: {result['score']}/2 ({result['score_explanation']})")
        
        # Display final scores
        print(f"\n" + "="*60)
        print("FINAL SCORING SUMMARY")
        print("="*60)
        
        company_questions = questions.get('company_specific_questions', [])
        problem_questions = questions.get('problem_based_questions', [])
        
        print(f"Company-Specific Questions Score: {scoring_results.get('company_specific_score', 0)}/{len(company_questions) * 2}")
        print(f"Problem-Based Questions Score: {scoring_results.get('problem_based_score', 0)}/{len(problem_questions) * 2}")
        print(f"TOTAL SCORE: {scoring_results.get('total_score', 0)}/{scoring_results.get('max_possible_score', 0)}")
        
        success_rate = scoring_results.get('success_rate', 0)
        print(f"SUCCESS RATE: {success_rate}%")
    
    print("\n" + "="*60)


def main():
    """
    Main function to run the website analyzer CLI
    """
    # Default website URL (can be changed or made configurable)
    website_url = "https://spacetil.com"
    
    # Allow URL to be passed as command line argument
    if len(sys.argv) > 1:
        website_url = sys.argv[1]
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: Please set your OPENAI_API_KEY environment variable")
        print("You can set it by running: export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Add https:// if not present
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url
    
    try:
        print(f"Analyzing website: {website_url}")
        print("This may take a few minutes as we test questions with OpenAI...")
        
        # Create analyzer instance
        analyzer = WebsiteAnalyzer(api_key)
        
        # Run complete analysis
        results = analyzer.analyze_website_complete(website_url)
        
        # Print results
        print_analysis_results(results)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()