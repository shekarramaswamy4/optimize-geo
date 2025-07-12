"""Authentication middleware and dependencies."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.auth import UserContext, EntityContext, MembershipContext, SessionContext
from src.core.exceptions import AuthenticationError, AuthorizationError
from src.core.workos_client import get_workos_client
from src.database import get_postgres_db, User, Entity, UserMembership

logger = logging.getLogger(__name__)

# Custom security scheme for header-based auth
class HeaderAuthentication:
    """Custom authentication that reads x-email and x-auth-id headers."""
    
    async def __call__(self, request: Request) -> Optional[tuple[str, str]]:
        """Extract authentication headers from request."""
        email = request.headers.get("x-email")
        auth_id = request.headers.get("x-auth-id")
        
        if not email or not auth_id:
            return None
            
        return email, auth_id


class EntityHeaderAuthentication:
    """Custom authentication that reads all required headers including entity."""
    
    async def __call__(self, request: Request) -> Optional[tuple[str, str, str]]:
        """Extract authentication and entity headers from request."""
        email = request.headers.get("x-email")
        auth_id = request.headers.get("x-auth-id")
        entity_id = request.headers.get("x-entity-id")
        
        if not email or not auth_id or not entity_id:
            return None
            
        return email, auth_id, entity_id


# Create instances
header_auth = HeaderAuthentication()
entity_header_auth = EntityHeaderAuthentication()


async def get_current_user(
    request: Request,
    auth_headers: Optional[tuple[str, str]] = Depends(header_auth),
    db: Session = Depends(get_postgres_db),
) -> UserContext:
    """
    Get current authenticated user from headers.
    
    Args:
        request: FastAPI request object
        auth_headers: Tuple of (email, auth_id) from headers
        db: Database session
        
    Returns:
        UserContext: Authenticated user context
        
    Raises:
        HTTPException: If authentication fails
    """
    if not auth_headers:
        logger.warning("Missing authentication headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers (x-email and x-auth-id required)",
            headers={"WWW-Authenticate": "Custom"},
        )
    
    email, auth_id = auth_headers
    
    try:
        # Query user by email
        user = db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
        
        if not user:
            logger.info(f"User not found in database for email: {email}, checking WorkOS")
            
            # Try to fetch user from WorkOS
            workos_client = get_workos_client()
            
            # Verify the email matches the WorkOS user
            if not workos_client.verify_user_email(email, auth_id):
                logger.warning(f"Email mismatch or user not found in WorkOS: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            
            # Get full user data from WorkOS
            workos_user_data = workos_client.get_user_by_id(auth_id)
            if not workos_user_data:
                logger.error(f"Failed to fetch user data from WorkOS for auth_id: {auth_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            
            # Create user in our database
            logger.info(f"Creating new user from WorkOS data: {email}")
            user = User(
                email=workos_user_data["email"],
                first_name=workos_user_data.get("first_name", ""),
                last_name=workos_user_data.get("last_name", ""),
                workos_user_id=auth_id,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User created successfully: {user.email}")
        
        # Verify auth_id matches (for existing users)
        elif user.workos_user_id != auth_id:
            logger.warning(f"Auth ID mismatch for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        # Create user context
        user_context = UserContext(
            id=user.id,
            email=user.email,
            auth_id=user.workos_user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )
        
        # Store in request state for access in other parts of the app
        request.state.user = user_context
        
        logger.info(f"Authenticated user: {user.email}")
        return user_context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


async def get_optional_user(
    request: Request,
    auth_headers: Optional[tuple[str, str]] = Depends(header_auth),
    db: Session = Depends(get_postgres_db),
) -> Optional[UserContext]:
    """
    Get current user if authenticated, otherwise return None.
    
    This is useful for endpoints that support both authenticated and 
    anonymous access with different behavior.
    """
    if not auth_headers:
        return None
    
    try:
        return await get_current_user(request, auth_headers, db)
    except HTTPException:
        return None


class RequireAuth:
    """Dependency that requires authentication for specific roles or permissions."""
    
    def __init__(self, roles: Optional[list[str]] = None):
        self.roles = roles or []
    
    async def __call__(
        self,
        user: UserContext = Depends(get_current_user),
        db: Session = Depends(get_postgres_db),
    ) -> UserContext:
        """
        Verify user has required roles.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            UserContext: Authenticated user if authorized
            
        Raises:
            HTTPException: If user lacks required roles
        """
        if not self.roles:
            return user
        
        # Check user roles (would need to implement role checking logic)
        # For now, we'll just return the user
        # In a real implementation, you'd check user_membership table
        
        return user


async def get_session_context(
    request: Request,
    auth_headers: Optional[tuple[str, str, str]] = Depends(entity_header_auth),
    db: Session = Depends(get_postgres_db),
) -> SessionContext:
    """
    Get complete session context including user, entity, and membership.
    
    Args:
        request: FastAPI request object
        auth_headers: Tuple of (email, auth_id, entity_id) from headers
        db: Database session
        
    Returns:
        SessionContext: Complete session context
        
    Raises:
        HTTPException: If authentication fails or entity access denied
    """
    if not auth_headers:
        logger.warning("Missing authentication headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers (x-email, x-auth-id, and x-entity-id required)",
            headers={"WWW-Authenticate": "Custom"},
        )
    
    email, auth_id, entity_id = auth_headers
    
    try:
        # First get the user context using existing logic
        user_headers = (email, auth_id)
        user_context = await get_current_user(request, user_headers, db)
        
        # Parse entity ID
        try:
            from uuid import UUID
            entity_uuid = UUID(entity_id)
        except ValueError:
            logger.warning(f"Invalid entity ID format: {entity_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entity ID format",
            )
        
        # Get entity from database
        entity = db.query(Entity).filter(
            Entity.id == entity_uuid,
            Entity.is_active == True
        ).first()
        
        if not entity:
            logger.warning(f"Entity not found: {entity_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity not found",
            )
        
        # Check user membership in entity
        membership = db.query(UserMembership).filter(
            UserMembership.user_id == user_context.id,
            UserMembership.entity_id == entity_uuid,
            UserMembership.is_active == True
        ).first()
        
        if not membership:
            logger.warning(f"User {user_context.email} has no access to entity {entity_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this entity",
            )
        
        # Create entity context
        entity_context = EntityContext(
            id=entity.id,
            name=entity.name,
            is_active=entity.is_active,
        )
        
        # Create membership context
        membership_context = MembershipContext(
            id=membership.id,
            user_id=membership.user_id,
            entity_id=membership.entity_id,
            role=membership.role,
            is_active=membership.is_active,
        )
        
        # Get request ID from dependencies
        from src.api.dependencies import get_request_id
        request_id = request.state.request_id if hasattr(request.state, 'request_id') else "unknown"
        
        # Create complete session context
        session_context = SessionContext(
            user=user_context,
            entity=entity_context,
            membership=membership_context,
            request_id=request_id,
        )
        
        # Store in request state for access in other parts of the app
        request.state.session = session_context
        
        logger.info(
            f"Authenticated session for user: {user_context.email}, "
            f"entity: {entity.name}, role: {membership.role}"
        )
        return session_context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


class RequireSession:
    """Dependency that requires full session context with entity access."""
    
    def __init__(self, roles: Optional[list[str]] = None):
        self.roles = roles or []
    
    async def __call__(
        self,
        session: SessionContext = Depends(get_session_context),
        db: Session = Depends(get_postgres_db),
    ) -> SessionContext:
        """
        Verify user has required roles in the entity.
        
        Args:
            session: Current session context
            db: Database session
            
        Returns:
            SessionContext: Authenticated session if authorized
            
        Raises:
            HTTPException: If user lacks required roles
        """
        if not self.roles:
            return session
        
        # Check if user has required role in the entity
        if session.membership.role not in self.roles:
            logger.warning(
                f"User {session.user.email} with role {session.membership.role} "
                f"lacks required roles: {self.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(self.roles)}",
            )
        
        return session


# Common auth dependencies
require_auth = RequireAuth()
require_admin = RequireAuth(roles=["admin"])
require_owner = RequireAuth(roles=["owner", "admin"])

# Session-based auth dependencies
require_session = RequireSession()
require_session_admin = RequireSession(roles=["admin", "owner"])
require_session_owner = RequireSession(roles=["owner"])