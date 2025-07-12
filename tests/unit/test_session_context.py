"""Unit tests for session context authentication."""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4, UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.api.auth import get_session_context, RequireSession
from src.core.auth import SessionContext, UserContext, EntityContext, MembershipContext
from src.database import User, Entity, UserMembership


class TestSessionContext:
    """Test cases for session context authentication."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object."""
        request = Mock()
        request.headers = {
            "x-email": "test@example.com",
            "x-auth-id": "user_12345",
            "x-entity-id": str(uuid4())
        }
        request.state = Mock()
        request.state.request_id = "req_123"
        return request
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            workos_user_id="user_12345",
            is_active=True,
        )
        return user
    
    @pytest.fixture
    def mock_entity(self):
        """Create a mock entity."""
        entity = Entity(
            id=uuid4(),
            name="Test Organization",
            is_active=True,
        )
        return entity
    
    @pytest.fixture
    def mock_membership(self, mock_user, mock_entity):
        """Create a mock membership."""
        membership = UserMembership(
            id=uuid4(),
            user_id=mock_user.id,
            entity_id=mock_entity.id,
            role="member",
            is_active=True,
        )
        return membership
    
    @pytest.mark.asyncio
    async def test_get_session_context_success(
        self, mock_db, mock_request, mock_user, mock_entity, mock_membership
    ):
        """Test successful session context creation."""
        # Setup headers
        entity_id = str(mock_entity.id)
        auth_headers = ("test@example.com", "user_12345", entity_id)
        mock_request.headers["x-entity-id"] = entity_id
        
        # Mock get_current_user to return user context
        user_context = UserContext(
            id=mock_user.id,
            email=mock_user.email,
            auth_id=mock_user.workos_user_id,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name,
            is_active=mock_user.is_active,
        )
        
        with patch("src.api.auth.get_current_user", return_value=user_context):
            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_entity,  # Entity query
                mock_membership,  # Membership query
            ]
            
            # Execute
            result = await get_session_context(mock_request, auth_headers, mock_db)
            
            # Verify result
            assert isinstance(result, SessionContext)
            assert result.user.email == "test@example.com"
            assert result.entity.name == "Test Organization"
            assert result.membership.role == "member"
            assert result.request_id == "req_123"
    
    @pytest.mark.asyncio
    async def test_get_session_context_missing_headers(self, mock_db, mock_request):
        """Test failure when authentication headers are missing."""
        auth_headers = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_session_context(mock_request, auth_headers, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Missing authentication headers" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_session_context_invalid_entity_id(self, mock_db, mock_request, mock_user):
        """Test failure when entity ID format is invalid."""
        auth_headers = ("test@example.com", "user_12345", "invalid-uuid")
        
        user_context = UserContext(
            id=mock_user.id,
            email=mock_user.email,
            auth_id=mock_user.workos_user_id,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name,
            is_active=mock_user.is_active,
        )
        
        with patch("src.api.auth.get_current_user", return_value=user_context):
            with pytest.raises(HTTPException) as exc_info:
                await get_session_context(mock_request, auth_headers, mock_db)
            
            assert exc_info.value.status_code == 400
            assert "Invalid entity ID format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_session_context_entity_not_found(self, mock_db, mock_request, mock_user):
        """Test failure when entity is not found."""
        entity_id = str(uuid4())
        auth_headers = ("test@example.com", "user_12345", entity_id)
        
        user_context = UserContext(
            id=mock_user.id,
            email=mock_user.email,
            auth_id=mock_user.workos_user_id,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name,
            is_active=mock_user.is_active,
        )
        
        with patch("src.api.auth.get_current_user", return_value=user_context):
            # Mock entity not found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_session_context(mock_request, auth_headers, mock_db)
            
            assert exc_info.value.status_code == 404
            assert "Entity not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_session_context_no_membership(
        self, mock_db, mock_request, mock_user, mock_entity
    ):
        """Test failure when user has no membership in entity."""
        entity_id = str(mock_entity.id)
        auth_headers = ("test@example.com", "user_12345", entity_id)
        
        user_context = UserContext(
            id=mock_user.id,
            email=mock_user.email,
            auth_id=mock_user.workos_user_id,
            first_name=mock_user.first_name,
            last_name=mock_user.last_name,
            is_active=mock_user.is_active,
        )
        
        with patch("src.api.auth.get_current_user", return_value=user_context):
            # Mock queries
            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_entity,  # Entity found
                None,  # No membership
            ]
            
            with pytest.raises(HTTPException) as exc_info:
                await get_session_context(mock_request, auth_headers, mock_db)
            
            assert exc_info.value.status_code == 403
            assert "Access denied to this entity" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_require_session_with_roles(self, mock_db):
        """Test RequireSession dependency with role requirements."""
        # Create session with admin role
        session = SessionContext(
            user=UserContext(
                id=uuid4(),
                email="admin@example.com",
                auth_id="user_admin",
                first_name="Admin",
                last_name="User",
                is_active=True,
            ),
            entity=EntityContext(
                id=uuid4(),
                name="Test Org",
                is_active=True,
            ),
            membership=MembershipContext(
                id=uuid4(),
                user_id=uuid4(),
                entity_id=uuid4(),
                role="admin",
                is_active=True,
            ),
            request_id="req_123",
        )
        
        # Test admin requirement - should pass
        require_admin = RequireSession(roles=["admin", "owner"])
        result = await require_admin(session, mock_db)
        assert result == session
        
        # Test owner requirement - should fail
        require_owner = RequireSession(roles=["owner"])
        with pytest.raises(HTTPException) as exc_info:
            await require_owner(session, mock_db)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)
    
    def test_session_context_properties(self):
        """Test SessionContext convenience properties."""
        user_id = uuid4()
        entity_id = uuid4()
        
        session = SessionContext(
            user=UserContext(
                id=user_id,
                email="test@example.com",
                auth_id="user_123",
                first_name="Test",
                last_name="User",
                is_active=True,
            ),
            entity=EntityContext(
                id=entity_id,
                name="Test Org",
                is_active=True,
            ),
            membership=MembershipContext(
                id=uuid4(),
                user_id=user_id,
                entity_id=entity_id,
                role="owner",
                is_active=True,
            ),
            request_id="req_123",
        )
        
        # Test convenience properties
        assert session.user_id == user_id
        assert session.entity_id == entity_id
        assert session.role == "owner"
        assert session.is_admin is True
        assert session.is_owner is True
    
    def test_membership_context_role_checks(self):
        """Test MembershipContext role checking methods."""
        # Test member role
        member = MembershipContext(
            id=uuid4(),
            user_id=uuid4(),
            entity_id=uuid4(),
            role="member",
            is_active=True,
        )
        assert member.is_admin is False
        assert member.is_owner is False
        
        # Test admin role
        admin = MembershipContext(
            id=uuid4(),
            user_id=uuid4(),
            entity_id=uuid4(),
            role="admin",
            is_active=True,
        )
        assert admin.is_admin is True
        assert admin.is_owner is False
        
        # Test owner role
        owner = MembershipContext(
            id=uuid4(),
            user_id=uuid4(),
            entity_id=uuid4(),
            role="owner",
            is_active=True,
        )
        assert owner.is_admin is True
        assert owner.is_owner is True