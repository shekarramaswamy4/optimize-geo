"""Unit tests for SQLAlchemy database models."""

import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.postgres.models import Base, User, Entity, UserMembership


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, in_memory_db):
        """Test creating a user instance."""
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            workos_user_id="workos_123"
        )
        
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.workos_user_id == "workos_123"
        assert user.is_active is True
        assert isinstance(user.id, uuid.UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_persistence(self, in_memory_db):
        """Test saving and retrieving a user."""
        user = User(
            email="persist@example.com",
            first_name="Persist",
            last_name="Test"
        )
        
        in_memory_db.add(user)
        in_memory_db.commit()
        
        # Retrieve user
        saved_user = in_memory_db.query(User).filter_by(email="persist@example.com").first()
        assert saved_user is not None
        assert saved_user.email == "persist@example.com"
        assert saved_user.first_name == "Persist"
        assert saved_user.last_name == "Test"
    
    def test_user_unique_email_constraint(self, in_memory_db):
        """Test that email uniqueness is enforced."""
        user1 = User(
            email="unique@example.com",
            first_name="User",
            last_name="One"
        )
        user2 = User(
            email="unique@example.com",
            first_name="User",
            last_name="Two"
        )
        
        in_memory_db.add(user1)
        in_memory_db.commit()
        
        in_memory_db.add(user2)
        with pytest.raises(Exception):  # SQLite raises IntegrityError
            in_memory_db.commit()
    
    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            id=uuid.uuid4(),
            email="repr@example.com",
            first_name="Repr",
            last_name="Test"
        )
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert "repr@example.com" in repr_str
        assert str(user.id) in repr_str
    
    def test_user_relationships(self, in_memory_db):
        """Test user relationships."""
        user = User(
            email="relations@example.com",
            first_name="Relations",
            last_name="Test"
        )
        entity = Entity(name="Test Entity")
        membership = UserMembership(
            user=user,
            entity=entity,
            role="admin"
        )
        
        in_memory_db.add_all([user, entity, membership])
        in_memory_db.commit()
        
        # Test relationship access
        assert len(user.memberships) == 1
        assert user.memberships[0].entity.name == "Test Entity"
        assert user.memberships[0].role == "admin"


class TestEntityModel:
    """Test Entity model functionality."""
    
    def test_entity_creation(self):
        """Test creating an entity instance."""
        entity = Entity(name="Test Organization")
        
        assert entity.name == "Test Organization"
        assert entity.is_active is True
        assert isinstance(entity.id, uuid.UUID)
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)
    
    def test_entity_persistence(self, in_memory_db):
        """Test saving and retrieving an entity."""
        entity = Entity(name="Persistent Org")
        
        in_memory_db.add(entity)
        in_memory_db.commit()
        
        # Retrieve entity
        saved_entity = in_memory_db.query(Entity).filter_by(name="Persistent Org").first()
        assert saved_entity is not None
        assert saved_entity.name == "Persistent Org"
    
    def test_entity_repr(self):
        """Test entity string representation."""
        entity = Entity(
            id=uuid.uuid4(),
            name="Test Org"
        )
        
        repr_str = repr(entity)
        assert "Entity" in repr_str
        assert "Test Org" in repr_str
        assert str(entity.id) in repr_str
    
    def test_entity_relationships(self, in_memory_db):
        """Test entity relationships."""
        entity = Entity(name="Relationship Org")
        user = User(
            email="entity@example.com",
            first_name="Entity",
            last_name="User"
        )
        membership = UserMembership(
            user=user,
            entity=entity,
            role="member"
        )
        
        in_memory_db.add_all([user, entity, membership])
        in_memory_db.commit()
        
        # Test relationship access
        assert len(entity.memberships) == 1
        assert entity.memberships[0].user.email == "entity@example.com"
        assert entity.memberships[0].role == "member"


class TestUserMembershipModel:
    """Test UserMembership model functionality."""
    
    def test_membership_creation(self):
        """Test creating a membership instance."""
        user_id = uuid.uuid4()
        entity_id = uuid.uuid4()
        
        membership = UserMembership(
            user_id=user_id,
            entity_id=entity_id,
            role="owner"
        )
        
        assert membership.user_id == user_id
        assert membership.entity_id == entity_id
        assert membership.role == "owner"
        assert membership.is_active is True
        assert isinstance(membership.id, uuid.UUID)
        assert isinstance(membership.created_at, datetime)
        assert isinstance(membership.updated_at, datetime)
    
    def test_membership_persistence(self, in_memory_db):
        """Test saving and retrieving a membership."""
        user = User(
            email="membership@example.com",
            first_name="Member",
            last_name="User"
        )
        entity = Entity(name="Member Org")
        membership = UserMembership(
            user=user,
            entity=entity,
            role="admin"
        )
        
        in_memory_db.add_all([user, entity, membership])
        in_memory_db.commit()
        
        # Retrieve membership
        saved_membership = in_memory_db.query(UserMembership).first()
        assert saved_membership is not None
        assert saved_membership.role == "admin"
        assert saved_membership.user.email == "membership@example.com"
        assert saved_membership.entity.name == "Member Org"
    
    def test_membership_cascade_delete_user(self, in_memory_db):
        """Test that membership is deleted when user is deleted."""
        user = User(
            email="cascade@example.com",
            first_name="Cascade",
            last_name="User"
        )
        entity = Entity(name="Cascade Org")
        membership = UserMembership(
            user=user,
            entity=entity,
            role="member"
        )
        
        in_memory_db.add_all([user, entity, membership])
        in_memory_db.commit()
        
        # Delete user
        in_memory_db.delete(user)
        in_memory_db.commit()
        
        # Verify membership is deleted
        remaining_memberships = in_memory_db.query(UserMembership).all()
        assert len(remaining_memberships) == 0
        
        # Verify entity still exists
        remaining_entity = in_memory_db.query(Entity).first()
        assert remaining_entity is not None
        assert remaining_entity.name == "Cascade Org"
    
    def test_membership_cascade_delete_entity(self, in_memory_db):
        """Test that membership is deleted when entity is deleted."""
        user = User(
            email="cascade2@example.com",
            first_name="Cascade2",
            last_name="User"
        )
        entity = Entity(name="Cascade2 Org")
        membership = UserMembership(
            user=user,
            entity=entity,
            role="member"
        )
        
        in_memory_db.add_all([user, entity, membership])
        in_memory_db.commit()
        
        # Delete entity
        in_memory_db.delete(entity)
        in_memory_db.commit()
        
        # Verify membership is deleted
        remaining_memberships = in_memory_db.query(UserMembership).all()
        assert len(remaining_memberships) == 0
        
        # Verify user still exists
        remaining_user = in_memory_db.query(User).first()
        assert remaining_user is not None
        assert remaining_user.email == "cascade2@example.com"
    
    def test_membership_repr(self):
        """Test membership string representation."""
        user_id = uuid.uuid4()
        entity_id = uuid.uuid4()
        membership = UserMembership(
            id=uuid.uuid4(),
            user_id=user_id,
            entity_id=entity_id,
            role="viewer"
        )
        
        repr_str = repr(membership)
        assert "UserMembership" in repr_str
        assert str(membership.id) in repr_str
        assert str(user_id) in repr_str
        assert str(entity_id) in repr_str
        assert "viewer" in repr_str
    
    def test_membership_default_role(self):
        """Test that default role is 'member'."""
        membership = UserMembership(
            user_id=uuid.uuid4(),
            entity_id=uuid.uuid4()
        )
        
        assert membership.role == "member"


class TestAuditColumns:
    """Test audit column functionality across all models."""
    
    def test_audit_columns_default_values(self):
        """Test that audit columns have proper defaults."""
        user = User(
            email="audit@example.com",
            first_name="Audit",
            last_name="Test"
        )
        
        assert user.is_active is True
        assert user.created_by is None
        assert user.updated_by is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_audit_columns_custom_values(self):
        """Test setting custom audit column values."""
        creator_id = uuid.uuid4()
        updater_id = uuid.uuid4()
        
        entity = Entity(
            name="Audit Entity",
            created_by=creator_id,
            updated_by=updater_id,
            is_active=False
        )
        
        assert entity.created_by == creator_id
        assert entity.updated_by == updater_id
        assert entity.is_active is False