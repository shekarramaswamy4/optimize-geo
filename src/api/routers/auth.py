"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, get_optional_user
from src.core.auth import UserContext
from src.database import get_postgres_db, User
from src.models.schemas import BaseResponse
from src.utils.logging import get_logger

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = get_logger(__name__)


class AuthCheckResponse(BaseResponse):
    """Response for auth check endpoint."""
    authenticated: bool
    user: UserContext | None = None


@router.get("/check", response_model=AuthCheckResponse)
async def check_auth(
    user: Annotated[UserContext | None, Depends(get_optional_user)],
) -> AuthCheckResponse:
    """
    Check if the current request is authenticated.
    
    Returns user information if authenticated, otherwise returns authenticated=false.
    """
    if user:
        logger.info(f"Auth check passed for user: {user.email}")
        return AuthCheckResponse(
            success=True,
            authenticated=True,
            user=user,
        )
    else:
        logger.info("Auth check failed - no valid credentials")
        return AuthCheckResponse(
            success=True,
            authenticated=False,
            user=None,
        )


class UserInfoResponse(BaseResponse):
    """Response for user info endpoint."""
    user: UserContext


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> UserInfoResponse:
    """
    Get current authenticated user information.
    
    Requires authentication.
    """
    return UserInfoResponse(
        success=True,
        user=current_user,
    )


class CreateUserRequest(BaseModel):
    """Request for creating a new user."""
    email: str
    auth_id: str
    first_name: str
    last_name: str


@router.post("/register", response_model=UserInfoResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: CreateUserRequest,
    db: Session = Depends(get_postgres_db),
) -> UserInfoResponse:
    """
    Register a new user.
    
    This endpoint is typically called after successful authentication with WorkOS
    or another auth provider to create the user record in our database.
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == request.email) | 
            (User.workos_user_id == request.auth_id)
        ).first()
        
        if existing_user:
            # If user exists but auth_id doesn't match, update it
            if existing_user.workos_user_id != request.auth_id:
                existing_user.workos_user_id = request.auth_id
                db.commit()
                db.refresh(existing_user)
            
            user_context = UserContext(
                id=existing_user.id,
                email=existing_user.email,
                auth_id=existing_user.workos_user_id,
                first_name=existing_user.first_name,
                last_name=existing_user.last_name,
                is_active=existing_user.is_active,
            )
            
            return UserInfoResponse(
                success=True,
                user=user_context,
            )
        
        # Create new user
        new_user = User(
            email=request.email,
            workos_user_id=request.auth_id,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        user_context = UserContext(
            id=new_user.id,
            email=new_user.email,
            auth_id=new_user.workos_user_id,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            is_active=new_user.is_active,
        )
        
        logger.info(f"New user registered: {new_user.email}")
        
        return UserInfoResponse(
            success=True,
            user=user_context,
        )
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )