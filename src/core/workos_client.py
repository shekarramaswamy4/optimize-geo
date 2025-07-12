"""WorkOS client configuration and utilities."""

import logging
from typing import Optional, Dict, Any

import workos
from workos.exceptions import BaseRequestException

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class WorkOSClient:
    """WorkOS client wrapper for user management."""
    
    def __init__(self):
        """Initialize WorkOS client with API key from settings."""
        settings = get_settings()
        
        # Configure WorkOS client if keys are provided
        if settings.workos_api_key and settings.workos_client_id:
            workos.api_key = settings.workos_api_key
            workos.client_id = settings.workos_client_id
        
        # Store settings for reference
        self.settings = settings
        
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user details from WorkOS by user ID.
        
        Args:
            user_id: WorkOS user ID (e.g., 'user_01234567890')
            
        Returns:
            User data dict or None if not found
        """
        # Return None if WorkOS is not configured
        if not self.settings.workos_api_key or not self.settings.workos_client_id:
            logger.warning("WorkOS not configured, skipping user lookup")
            return None
            
        try:
            # Get user from WorkOS using user management API
            user = workos.user_management.get_user(user_id)
            
            if not user:
                logger.warning(f"User not found in WorkOS: {user_id}")
                return None
            
            # Extract user data
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "email_verified": user.email_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            
            logger.info(f"Retrieved user from WorkOS: {user.email}")
            return user_data
            
        except BaseRequestException as e:
            logger.error(f"WorkOS API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user from WorkOS: {e}")
            return None
    
    def verify_user_email(self, email: str, auth_id: str) -> bool:
        """
        Verify that the provided email matches the WorkOS user.
        
        Args:
            email: Email address to verify
            auth_id: WorkOS user ID
            
        Returns:
            True if email matches, False otherwise
        """
        try:
            user_data = self.get_user_by_id(auth_id)
            if not user_data:
                return False
                
            return user_data.get("email", "").lower() == email.lower()
            
        except Exception as e:
            logger.error(f"Error verifying user email: {e}")
            return False


# Singleton instance
_workos_client: Optional[WorkOSClient] = None


def get_workos_client() -> WorkOSClient:
    """Get or create WorkOS client singleton."""
    global _workos_client
    
    if _workos_client is None:
        _workos_client = WorkOSClient()
    
    return _workos_client