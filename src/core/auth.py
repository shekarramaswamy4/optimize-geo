"""Authentication and user context management."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserContext(BaseModel):
    """User context for authenticated requests."""
    
    id: UUID
    email: EmailStr
    auth_id: str
    first_name: str
    last_name: str
    is_active: bool = True
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get user's display name (email if name not available)."""
        if self.first_name or self.last_name:
            return self.full_name.strip()
        return self.email
    
    class Config:
        frozen = True  # Make immutable


class EntityContext(BaseModel):
    """Entity context for authenticated requests."""
    
    id: UUID
    name: str
    is_active: bool = True
    
    class Config:
        frozen = True


class MembershipContext(BaseModel):
    """User membership context for authenticated requests."""
    
    id: UUID
    user_id: UUID
    entity_id: UUID
    role: str
    is_active: bool = True
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role in ["admin", "owner"]
    
    @property
    def is_owner(self) -> bool:
        """Check if user has owner role."""
        return self.role == "owner"
    
    class Config:
        frozen = True


class SessionContext(BaseModel):
    """Complete session context including user, entity, and membership."""
    
    user: UserContext
    entity: EntityContext
    membership: MembershipContext
    request_id: str
    
    @property
    def user_id(self) -> UUID:
        """Shortcut to user ID."""
        return self.user.id
    
    @property
    def entity_id(self) -> UUID:
        """Shortcut to entity ID."""
        return self.entity.id
    
    @property
    def role(self) -> str:
        """Shortcut to user's role in entity."""
        return self.membership.role
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.membership.is_admin
    
    @property
    def is_owner(self) -> bool:
        """Check if user is owner."""
        return self.membership.is_owner
    
    class Config:
        frozen = True