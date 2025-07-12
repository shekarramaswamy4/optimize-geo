#!/usr/bin/env python3
"""Script to run the FastAPI server with Uvicorn."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

from src.config.settings import get_settings


def main():
    """Run the FastAPI application."""
    settings = get_settings()
    
    # Configure uvicorn
    config = {
        "app": "src.main:app",
        "host": settings.host,
        "port": settings.port,
        "workers": settings.workers if not settings.reload else 1,
        "reload": settings.reload,
        "log_level": settings.log_level.lower(),
        "access_log": settings.is_development,
    }
    
    # Add SSL configuration if needed
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        config.update({
            "ssl_keyfile": "key.pem",
            "ssl_certfile": "cert.pem",
        })
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Server: http://{settings.host}:{settings.port}")
    
    if settings.is_development:
        print(f"Documentation: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(**config)


if __name__ == "__main__":
    main()