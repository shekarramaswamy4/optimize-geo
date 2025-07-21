"""
OpenAI Function Calling Tools
Extensible tool system for web search, news, and other external data sources
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class Tool(ABC):
    """Abstract base class for OpenAI function calling tools"""
    
    @abstractmethod
    def get_function_definition(self) -> Dict[str, Any]:
        """Return the function definition for OpenAI function calling"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with the provided arguments"""
        pass


class WebSearchTool(Tool):
    """Tool for searching the web using Serper API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def get_function_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for current information about a company or product",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to execute"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return (default: 10)"
                        }
                    },
                    "required": ["query", "num_results"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    
    def execute(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Execute web search using Serper API"""
        if not self.api_key:
            return {"error": "Web search API key not configured"}
        
        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": self.api_key},
                json={"q": query, "num": num_results},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format results for better readability
            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results)
            }
            
        except Exception as e:
            return {"error": f"Web search failed: {str(e)}"}


class NewsTool(Tool):
    """Tool for fetching recent news using NewsAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def get_function_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_recent_news",
                "description": "Get recent news articles about a specific topic or company",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic or company to search for in news articles"
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days back to search (default: 28)"
                        },
                        "max_articles": {
                            "type": "integer",
                            "description": "Maximum number of articles to return (default: 5)"
                        }
                    },
                    "required": ["topic", "days_back", "max_articles"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    
    def execute(self, topic: str, days_back: int = 28, max_articles: int = 5) -> Dict[str, Any]:
        """Execute news search using NewsAPI"""
        if not self.api_key:
            return {"error": "News API key not configured"}
        
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": topic,
                    "from": from_date,
                    "sortBy": "publishedAt",
                    "apiKey": self.api_key,
                    "pageSize": max_articles,
                    "language": "en"
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            articles = []
            for article in data.get("articles", [])[:max_articles]:
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "source": article.get("source", {}).get("name", "")
                })
            
            return {
                "success": True,
                "topic": topic,
                "articles": articles,
                "total_articles": len(articles)
            }
            
        except Exception as e:
            return {"error": f"News search failed: {str(e)}"}


class TavilyTool(Tool):
    """Tool for AI-optimized search and news using Tavily API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    def get_function_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "Search the web for current information, news, and company data using AI-optimized search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to execute"
                        },
                        "search_depth": {
                            "type": "string",
                            "description": "Search depth: 'basic' for quick results or 'advanced' for comprehensive search",
                            "enum": ["basic", "advanced"]
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 5)"
                        },
                        "include_answer": {
                            "type": "boolean",
                            "description": "Whether to include a summarized answer (default: true)"
                        },
                        "include_images": {
                            "type": "boolean", 
                            "description": "Whether to include relevant images (default: false)"
                        },
                        "include_raw_content": {
                            "type": "boolean",
                            "description": "Whether to include raw page content (default: false)"
                        }
                    },
                    "required": ["query", "search_depth", "max_results", "include_answer", "include_images", "include_raw_content"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    
    def execute(self, query: str, search_depth: str = "basic", max_results: int = 5, 
                include_answer: bool = True, include_images: bool = False, 
                include_raw_content: bool = False) -> Dict[str, Any]:
        """Execute search using Tavily API"""
        if not self.api_key:
            return {"error": "Tavily API key not configured"}
        
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "include_answer": include_answer,
                "include_images": include_images,
                "include_raw_content": include_raw_content
            }
            
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format results for better readability
            formatted_results = {
                "success": True,
                "query": query,
                "answer": data.get("answer", ""),
                "results": [],
                "total_results": len(data.get("results", []))
            }
            
            for item in data.get("results", []):
                formatted_results["results"].append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                    "published_date": item.get("published_date", "")
                })
            
            if include_images and data.get("images"):
                formatted_results["images"] = data.get("images", [])
            
            return formatted_results
            
        except Exception as e:
            return {"error": f"Tavily search failed: {str(e)}"}


class ToolManager:
    """Manages available tools and handles function calling execution"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the manager"""
        func_def = tool.get_function_definition()
        self.tools[func_def["function"]["name"]] = tool
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get all function definitions for OpenAI function calling"""
        return [tool.get_function_definition() for tool in self.tools.values()]
    
    def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with the provided arguments"""
        if function_name not in self.tools:
            return {"error": f"Unknown function: {function_name}"}
        
        try:
            return self.tools[function_name].execute(**arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
