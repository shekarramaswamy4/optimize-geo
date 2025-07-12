#!/usr/bin/env python3
"""
Website Analyzer Web Server
Flask API that analyzes websites using the shared library
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from website_analyzer_lib import WebsiteAnalyzer

app = Flask(__name__)
CORS(app)


@app.route('/analyze', methods=['POST'])
def analyze_website():
    """
    Main API endpoint to analyze a website
    
    Request body:
    {
        "website_url": "https://example.com",
        "company_name": "Optional Company Name"  // Optional, will be extracted from URL if not provided
    }
    
    Returns:
    {
        "success": true,
        "website_url": "https://example.com",
        "company_name": "Example",
        "analysis": {...},
        "questions": {...},
        "scoring_results": {...}
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'website_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'website_url' in request body"
            }), 400
        
        website_url = data['website_url']
        company_name = data.get('company_name')  # Optional
        
        # Validate URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "OpenAI API key not configured on server"
            }), 500
        
        # Create analyzer instance
        analyzer = WebsiteAnalyzer(api_key)
        
        # Run complete analysis
        results = analyzer.analyze_website_complete(website_url, company_name)
        
        # Add success flag
        results["success"] = True
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/analyze/quick', methods=['POST'])
def analyze_website_quick():
    """
    Quick analysis endpoint that skips question testing for faster results
    
    Request body:
    {
        "website_url": "https://example.com",
        "company_name": "Optional Company Name"
    }
    
    Returns:
    {
        "success": true,
        "website_url": "https://example.com", 
        "company_name": "Example",
        "analysis": {...},
        "questions": {...}
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'website_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'website_url' in request body"
            }), 400
        
        website_url = data['website_url']
        company_name = data.get('company_name')
        
        # Validate URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "OpenAI API key not configured on server"
            }), 500
        
        # Create analyzer instance
        analyzer = WebsiteAnalyzer(api_key)
        
        # Extract company name from URL if not provided
        if not company_name:
            company_name = analyzer.extract_company_name_from_url(website_url)
        
        # Fetch and analyze content
        content = analyzer.fetch_website_content(website_url)
        analysis = analyzer.analyze_website_content(content)
        
        # Generate questions only (no testing)
        questions = analyzer.generate_search_questions(analysis, company_name)
        
        return jsonify({
            "success": True,
            "website_url": website_url,
            "company_name": company_name,
            "analysis": analysis,
            "questions": questions
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/test-questions', methods=['POST'])
def test_questions():
    """
    Test questions against OpenAI and return scoring results
    
    Request body:
    {
        "questions": {
            "company_specific_questions": [...],
            "problem_based_questions": [...]
        },
        "company_name": "Company Name"
    }
    
    Returns:
    {
        "success": true,
        "scoring_results": {...}
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'questions' not in data or 'company_name' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'questions' or 'company_name' in request body"
            }), 400
        
        questions = data['questions']
        company_name = data['company_name']
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                "success": False,
                "error": "OpenAI API key not configured on server"
            }), 500
        
        # Create analyzer instance
        analyzer = WebsiteAnalyzer(api_key)
        
        # Test questions and get scoring results
        scoring_results = analyzer.test_questions_with_scoring(questions, company_name)
        
        return jsonify({
            "success": True,
            "scoring_results": scoring_results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "message": "Website Analyzer API is running",
        "version": "2.0"
    })


@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with API documentation
    """
    return jsonify({
        "message": "Website Analyzer API v2.0",
        "description": "Analyze websites and generate customer search questions with scoring",
        "endpoints": {
            "POST /analyze": {
                "description": "Complete website analysis with question testing and scoring",
                "body": {
                    "website_url": "string (required) - URL of the website to analyze",
                    "company_name": "string (optional) - Company name, will be extracted from URL if not provided"
                },
                "example": {
                    "website_url": "https://example.com",
                    "company_name": "Example Inc"
                },
                "note": "This endpoint takes longer as it tests questions against OpenAI"
            },
            "POST /analyze/quick": {
                "description": "Quick website analysis without question testing",
                "body": {
                    "website_url": "string (required) - URL of the website to analyze", 
                    "company_name": "string (optional) - Company name"
                },
                "example": {
                    "website_url": "https://example.com"
                },
                "note": "Faster response, generates questions but doesn't test them"
            },
            "POST /test-questions": {
                "description": "Test pre-generated questions against OpenAI and return scores",
                "body": {
                    "questions": "object (required) - Questions object with company_specific_questions and problem_based_questions arrays",
                    "company_name": "string (required) - Company name for scoring"
                },
                "note": "Use this to test questions generated from /analyze/quick"
            },
            "GET /health": {
                "description": "Health check endpoint"
            }
        },
        "usage": {
            "workflow_1": "Use POST /analyze for complete analysis (slower but comprehensive)",
            "workflow_2": "Use POST /analyze/quick then POST /test-questions for modular approach"
        }
    })


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors
    """
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "Visit GET / for API documentation"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors
    """
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Website Analyzer Server on port {port}")
    print(f"Debug mode: {debug}")
    print("Make sure OPENAI_API_KEY environment variable is set")
    
    app.run(host='0.0.0.0', port=port, debug=debug)