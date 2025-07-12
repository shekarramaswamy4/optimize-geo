"""Unit tests for authentication functionality."""

import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.auth import (
    HeaderAuthentication,
    get_current_user,
    get_optional_user,
    RequireAuth,
)
from src.core.auth import UserContext
from src.database import User


class TestHeaderAuthentication:
    """Test HeaderAuthentication class."""
    
    @pytest.mark.asyncio
    async def test_extract_valid_headers(self):
        """Test extracting valid authentication headers."""
        auth = HeaderAuthentication()
        
        # Mock request with headers
        request = Mock(spec=Request)
        request.headers = {
            "x-email": "test@example.com",
            "x-auth-id": "auth123",
        }
        
        result = await auth(request)
        assert result == ("test@example.com", "auth123")
    
    @pytest.mark.asyncio
    async def test_missing_email_header(self):
        """Test when email header is missing."""
        auth = HeaderAuthentication()
        
        request = Mock(spec=Request)
        request.headers = {"x-auth-id": "auth123"}
        
        result = await auth(request)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_missing_auth_id_header(self):
        """Test when auth-id header is missing."""
        auth = HeaderAuthentication()
        
        request = Mock(spec=Request)
        request.headers = {"x-email": "test@example.com"}
        
        result = await auth(request)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_missing_both_headers(self):
        """Test when both headers are missing."""
        auth = HeaderAuthentication()
        
        request = Mock(spec=Request)
        request.headers = {}
        
        result = await auth(request)
        assert result is None


class TestGetCurrentUser:
    """Test get_current_user function."""
    
    @pytest.mark.asyncio
    async def test_valid_authentication(self):
        """Test successful authentication with valid credentials."""
        # Mock request
        request = Mock(spec=Request)
        request.state = Mock()
        
        # Mock database session
        mock_db = Mock(spec=Session)
        
        # Mock user
        user_id = uuid.uuid4()
        mock_user = User(
            id=user_id,
            email="test@example.com",
            workos_user_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        # Setup query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        # Call function
        result = await get_current_user(
            request,
            auth_headers=("test@example.com", "auth123"),
            db=mock_db,
        )
        
        # Verify result
        assert isinstance(result, UserContext)
        assert result.id == user_id
        assert result.email == "test@example.com"
        assert result.auth_id == "auth123"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.is_active is True
        
        # Verify user was stored in request state
        assert request.state.user == result
    
    @pytest.mark.asyncio
    async def test_missing_headers(self):
        """Test authentication fails when headers are missing."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, auth_headers=None, db=mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing authentication headers" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_user_not_found(self):
        """Test authentication fails when user doesn't exist."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        # Setup query mock to return None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request,
                auth_headers=("test@example.com", "auth123"),
                db=mock_db,
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_auth_id_mismatch(self):
        """Test authentication fails when auth_id doesn't match."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        # Mock user with different auth_id
        mock_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            workos_user_id="different_auth_id",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        # Setup query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request,
                auth_headers=("test@example.com", "auth123"),
                db=mock_db,
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_inactive_user(self):
        """Test authentication fails for inactive users."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        # Mock inactive user - should not be returned by query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Query filters out inactive users
        mock_db.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request,
                auth_headers=("test@example.com", "auth123"),
                db=mock_db,
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetOptionalUser:
    """Test get_optional_user function."""
    
    @pytest.mark.asyncio
    async def test_with_valid_auth(self):
        """Test returns user when authenticated."""
        request = Mock(spec=Request)
        request.state = Mock()
        mock_db = Mock(spec=Session)
        
        # Mock user
        user_id = uuid.uuid4()
        mock_user = User(
            id=user_id,
            email="test@example.com",
            workos_user_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        # Setup query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = await get_optional_user(
            request,
            auth_headers=("test@example.com", "auth123"),
            db=mock_db,
        )
        
        assert isinstance(result, UserContext)
        assert result.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_without_auth(self):
        """Test returns None when not authenticated."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        result = await get_optional_user(
            request,
            auth_headers=None,
            db=mock_db,
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_with_invalid_auth(self):
        """Test returns None when authentication fails."""
        request = Mock(spec=Request)
        mock_db = Mock(spec=Session)
        
        # Setup query mock to return None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = await get_optional_user(
            request,
            auth_headers=("test@example.com", "invalid"),
            db=mock_db,
        )
        
        assert result is None


class TestRequireAuth:
    """Test RequireAuth dependency."""
    
    @pytest.mark.asyncio
    async def test_no_roles_required(self):
        """Test when no specific roles are required."""
        require_auth = RequireAuth()
        
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        mock_db = Mock(spec=Session)
        
        result = await require_auth(user, mock_db)
        assert result == user
    
    @pytest.mark.asyncio
    async def test_with_roles_required(self):
        """Test when specific roles are required."""
        # For now, this just returns the user
        # In a real implementation, it would check user_membership table
        require_admin = RequireAuth(roles=["admin"])
        
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        mock_db = Mock(spec=Session)
        
        result = await require_admin(user, mock_db)
        assert result == user


class TestUserContext:
    """Test UserContext model."""
    
    def test_full_name(self):
        """Test full_name property."""
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        assert user.full_name == "Test User"
    
    def test_display_name_with_name(self):
        """Test display_name when name is available."""
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        assert user.display_name == "Test User"
    
    def test_display_name_without_name(self):
        """Test display_name falls back to email."""
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="",
            last_name="",
            is_active=True,
        )
        
        assert user.display_name == "test@example.com"
    
    def test_immutability(self):
        """Test that UserContext is immutable."""
        user = UserContext(
            id=uuid.uuid4(),
            email="test@example.com",
            auth_id="auth123",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        
        # In Pydantic v2, frozen models raise ValidationError
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            user.email = "new@example.com"