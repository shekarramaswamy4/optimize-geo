"""Test data fixtures for unit and integration tests."""

# Sample website HTML content
SAMPLE_WEBSITE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TechCorp - Cloud Solutions for Enterprise</title>
</head>
<body>
    <h1>Welcome to TechCorp</h1>
    <p>We are a leading provider of cloud infrastructure solutions for enterprise customers.</p>
    
    <section>
        <h2>About Us</h2>
        <p>TechCorp specializes in scalable cloud solutions that help businesses transform their operations.</p>
    </section>
    
    <section>
        <h2>Our Features</h2>
        <ul>
            <li>Auto-scaling infrastructure</li>
            <li>99.99% uptime guarantee</li>
            <li>Enterprise-grade security</li>
            <li>24/7 support</li>
        </ul>
    </section>
    
    <section>
        <h2>Pricing</h2>
        <p>Starting at $999/month for our basic plan. Enterprise plans available.</p>
    </section>
    
    <section>
        <h2>Our Customers</h2>
        <p>Trusted by Fortune 500 companies and growing startups alike.</p>
    </section>
</body>
</html>
"""

# Expected extracted text
SAMPLE_WEBSITE_TEXT = """Welcome to TechCorp We are a leading provider of cloud infrastructure solutions for enterprise customers. About Us TechCorp specializes in scalable cloud solutions that help businesses transform their operations. Our Features Auto-scaling infrastructure 99.99% uptime guarantee Enterprise-grade security 24/7 support Pricing Starting at $999/month for our basic plan. Enterprise plans available. Our Customers Trusted by Fortune 500 companies and growing startups alike."""

# Sample company analysis response
SAMPLE_COMPANY_ANALYSIS = {
    "name": "TechCorp",
    "description": "TechCorp is a leading provider of cloud infrastructure solutions for enterprise customers. They specialize in scalable cloud solutions that help businesses transform their operations.",
    "ideal_customer_profile": "Fortune 500 companies and growing startups looking for enterprise-grade cloud infrastructure",
    "key_features": [
        "Auto-scaling infrastructure",
        "99.99% uptime guarantee",
        "Enterprise-grade security",
        "24/7 support"
    ],
    "pricing_info": "Starting at $999/month for basic plan, with enterprise plans available",
    "industry": "Cloud Infrastructure"
}

# Sample generated questions
SAMPLE_QUESTIONS = {
    "company_specific": [
        {
            "question": "What are TechCorp cloud infrastructure reviews?",
            "intent": "Research customer feedback and experiences"
        },
        {
            "question": "How does TechCorp compare to AWS?",
            "intent": "Compare with competitors"
        },
        {
            "question": "What is TechCorp pricing for enterprise?",
            "intent": "Understand pricing structure"
        },
        {
            "question": "Is TechCorp secure for financial data?",
            "intent": "Evaluate security capabilities"
        }
    ],
    "problem_based": [
        {
            "question": "Best cloud infrastructure for enterprise scalability",
            "intent": "Find scalable solutions"
        },
        {
            "question": "How to ensure 99.99% uptime for web applications",
            "intent": "Solve reliability issues"
        },
        {
            "question": "Enterprise cloud security best practices",
            "intent": "Learn about security"
        },
        {
            "question": "Auto-scaling infrastructure providers comparison",
            "intent": "Research auto-scaling options"
        },
        {
            "question": "24/7 cloud support services cost",
            "intent": "Understand support options"
        }
    ]
}

# Sample OpenAI responses for testing
SAMPLE_OPENAI_RESPONSES = {
    "company_specific_good": "TechCorp offers comprehensive cloud infrastructure solutions with auto-scaling capabilities, 99.99% uptime guarantee, and enterprise-grade security. Their pricing starts at $999/month for basic plans, with custom enterprise packages available. Many Fortune 500 companies rely on TechCorp for their critical infrastructure needs.",
    
    "company_specific_moderate": "Cloud infrastructure providers offer various solutions. Companies in this space typically provide scaling and security features.",
    
    "company_specific_poor": "I don't have specific information about that.",
    
    "problem_based_mentions_first": "TechCorp is a leading solution for enterprise cloud infrastructure scalability. They offer auto-scaling features that automatically adjust resources based on demand.",
    
    "problem_based_mentions_later": "For enterprise scalability, you'll want to look for providers with auto-scaling capabilities. AWS, Azure, and TechCorp all offer such features.",
    
    "problem_based_no_mention": "Enterprise cloud scalability requires auto-scaling infrastructure that can handle varying loads. Look for providers offering automatic resource adjustment and load balancing."
}

# Error responses
ERROR_RESPONSES = {
    "timeout": "Error: Request timeout",
    "invalid_json": "{invalid json}",
    "empty": "",
    "html_error": "<html><body>404 Not Found</body></html>"
}