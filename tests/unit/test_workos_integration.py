"""Unit tests for WorkOS integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.core.auth import UserContext
from src.database import User


class TestWorkOSIntegration:
    """Test cases for WorkOS user authentication and creation."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        return db
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock()
        request.headers = {"x-email": "test@example.com", "x-auth-id": "user_12345"}
        request.state = Mock()
        return request
    
    @pytest.fixture
    def mock_workos_client(self):
        """Create a mock WorkOS client."""
        with patch("src.api.auth.get_workos_client") as mock_get_client:
            client = Mock()
            mock_get_client.return_value = client
            yield client
    
    @pytest.mark.asyncio
    async def test_create_user_from_workos_successful(
        self, mock_db, mock_request, mock_workos_client
    ):
        """Test successful user creation from WorkOS data."""
        # Setup WorkOS mock responses
        mock_workos_client.verify_user_email.return_value = True
        mock_workos_client.get_user_by_id.return_value = {
            "id": "user_12345",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "email_verified": True,
        }
        
        # Mock the database add/commit/refresh
        created_user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            workos_user_id="user_12345",
            is_active=True,
        )
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda user: setattr(user, 'id', created_user.id))
        
        # Execute the authentication
        auth_headers = ("test@example.com", "user_12345")
        result = await get_current_user(mock_request, auth_headers, mock_db)
        
        # Verify WorkOS client was called
        mock_workos_client.verify_user_email.assert_called_once_with(
            "test@example.com", "user_12345"
        )
        mock_workos_client.get_user_by_id.assert_called_once_with("user_12345")
        
        # Verify user was created in database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the returned user context
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"
        assert result.auth_id == "user_12345"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_workos_email_mismatch(
        self, mock_db, mock_request, mock_workos_client
    ):
        """Test authentication failure when WorkOS email doesn't match."""
        # Setup WorkOS mock to return email mismatch
        mock_workos_client.verify_user_email.return_value = False
        
        # Execute and expect failure
        auth_headers = ("test@example.com", "user_12345")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, auth_headers, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)
        
        # Verify WorkOS client was called
        mock_workos_client.verify_user_email.assert_called_once_with(
            "test@example.com", "user_12345"
        )
        # Should not proceed to get_user_by_id
        mock_workos_client.get_user_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workos_user_not_found(
        self, mock_db, mock_request, mock_workos_client
    ):
        """Test authentication failure when WorkOS user data cannot be fetched."""
        # Setup WorkOS mock responses
        mock_workos_client.verify_user_email.return_value = True
        mock_workos_client.get_user_by_id.return_value = None  # User not found
        
        # Execute and expect failure
        auth_headers = ("test@example.com", "user_12345")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, auth_headers, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_existing_user_auth_success(
        self, mock_db, mock_request, mock_workos_client
    ):
        """Test successful authentication for existing user."""
        # Setup existing user in database
        existing_user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            workos_user_id="user_12345",
            is_active=True,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Execute authentication
        auth_headers = ("test@example.com", "user_12345")
        result = await get_current_user(mock_request, auth_headers, mock_db)
        
        # WorkOS should not be called for existing users
        mock_workos_client.verify_user_email.assert_not_called()
        mock_workos_client.get_user_by_id.assert_not_called()
        
        # Verify the returned user context
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"
        assert result.auth_id == "user_12345"
    
    @pytest.mark.asyncio
    async def test_existing_user_auth_id_mismatch(
        self, mock_db, mock_request, mock_workos_client
    ):
        """Test authentication failure when auth ID doesn't match for existing user."""
        # Setup existing user with different auth_id
        existing_user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            workos_user_id="different_user_id",
            is_active=True,
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        # Execute and expect failure
        auth_headers = ("test@example.com", "user_12345")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, auth_headers, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)