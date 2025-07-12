"""Unit tests for Alembic migration functionality."""

import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

# Import migration modules dynamically to test read_sql_file function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "alembic" / "versions"))


class TestMigrationHelpers:
    """Test migration helper functions."""
    
    def test_read_sql_file_success(self):
        """Test successfully reading SQL file."""
        # Import one of the migration modules
        from a1dff0914356_create_users_table import read_sql_file
        
        sql_content = "CREATE TABLE test (id INT);"
        
        with patch("builtins.open", mock_open(read_data=sql_content)):
            with patch("pathlib.Path.exists", return_value=True):
                result = read_sql_file("test.sql")
                assert result == sql_content
    
    def test_read_sql_file_not_found(self):
        """Test error when SQL file doesn't exist."""
        from a1dff0914356_create_users_table import read_sql_file
        
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                read_sql_file("nonexistent.sql")
            
            assert "SQL file not found" in str(exc_info.value)
    
    def test_sql_file_path_construction(self):
        """Test that SQL file path is constructed correctly."""
        from a1dff0914356_create_users_table import read_sql_file
        
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                read_sql_file("test.sql")
            
            error_message = str(exc_info.value)
            assert "sql/test.sql" in error_message


class TestUsersMigration:
    """Test users table migration."""
    
    @patch('alembic.op.execute')
    def test_users_upgrade(self, mock_execute):
        """Test users table upgrade migration."""
        from a1dff0914356_create_users_table import upgrade
        
        expected_sql = "CREATE TABLE IF NOT EXISTS users"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                upgrade()
        
        mock_execute.assert_called_once_with(expected_sql)
    
    @patch('alembic.op.execute')
    def test_users_downgrade(self, mock_execute):
        """Test users table downgrade migration."""
        from a1dff0914356_create_users_table import downgrade
        
        expected_sql = "DROP TABLE IF EXISTS users CASCADE"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                downgrade()
        
        mock_execute.assert_called_once_with(expected_sql)


class TestEntityMigration:
    """Test entity table migration."""
    
    @patch('alembic.op.execute')
    def test_entity_upgrade(self, mock_execute):
        """Test entity table upgrade migration."""
        # Import using importlib due to module name starting with number
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "entity_migration",
            Path(__file__).parent.parent.parent / "alembic" / "versions" / "0398f0f9a348_create_entity_table.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        expected_sql = "CREATE TABLE IF NOT EXISTS entity"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                module.upgrade()
        
        mock_execute.assert_called_once_with(expected_sql)
    
    @patch('alembic.op.execute')
    def test_entity_downgrade(self, mock_execute):
        """Test entity table downgrade migration."""
        # Import using importlib due to module name starting with number
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "entity_migration",
            Path(__file__).parent.parent.parent / "alembic" / "versions" / "0398f0f9a348_create_entity_table.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        expected_sql = "DROP TABLE IF EXISTS entity CASCADE"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                module.downgrade()
        
        mock_execute.assert_called_once_with(expected_sql)


class TestUserMembershipMigration:
    """Test user_membership table migration."""
    
    @patch('alembic.op.execute')
    def test_user_membership_upgrade(self, mock_execute):
        """Test user_membership table upgrade migration."""
        from b55d64201412_create_user_membership_table import upgrade
        
        expected_sql = "CREATE TABLE IF NOT EXISTS user_membership"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                upgrade()
        
        mock_execute.assert_called_once_with(expected_sql)
    
    @patch('alembic.op.execute')
    def test_user_membership_downgrade(self, mock_execute):
        """Test user_membership table downgrade migration."""
        from b55d64201412_create_user_membership_table import downgrade
        
        expected_sql = "DROP TABLE IF EXISTS user_membership CASCADE"
        
        with patch("builtins.open", mock_open(read_data=expected_sql)):
            with patch("pathlib.Path.exists", return_value=True):
                downgrade()
        
        mock_execute.assert_called_once_with(expected_sql)


class TestSQLFiles:
    """Test the actual SQL file contents."""
    
    def test_users_upgrade_sql_content(self):
        """Test users upgrade SQL has required elements."""
        sql_path = Path(__file__).parent.parent.parent / "alembic" / "sql" / "001_create_users_table_upgrade.sql"
        
        if sql_path.exists():
            content = sql_path.read_text()
            
            # Check for required table elements
            assert "CREATE TABLE IF NOT EXISTS users" in content
            assert "id UUID PRIMARY KEY" in content
            assert "email VARCHAR(255) UNIQUE NOT NULL" in content
            assert "first_name VARCHAR(100) NOT NULL" in content
            assert "last_name VARCHAR(100) NOT NULL" in content
            assert "workos_user_id VARCHAR(255)" in content
            assert "created_at TIMESTAMP" in content
            assert "updated_at TIMESTAMP" in content
            assert "is_active BOOLEAN" in content
            
            # Check for indexes
            assert "CREATE INDEX idx_users_email" in content
            assert "CREATE INDEX idx_users_workos_user_id" in content
            
            # Check for trigger
            assert "CREATE TRIGGER update_users_updated_at" in content
    
    def test_entity_upgrade_sql_content(self):
        """Test entity upgrade SQL has required elements."""
        sql_path = Path(__file__).parent.parent.parent / "alembic" / "sql" / "002_create_entity_table_upgrade.sql"
        
        if sql_path.exists():
            content = sql_path.read_text()
            
            # Check for required table elements
            assert "CREATE TABLE IF NOT EXISTS entity" in content
            assert "id UUID PRIMARY KEY" in content
            assert "name VARCHAR(255) NOT NULL" in content
            assert "created_at TIMESTAMP" in content
            assert "updated_at TIMESTAMP" in content
            assert "is_active BOOLEAN" in content
            
            # Check for indexes
            assert "CREATE INDEX idx_entity_name" in content
            
            # Check for trigger
            assert "CREATE TRIGGER update_entity_updated_at" in content
    
    def test_user_membership_upgrade_sql_content(self):
        """Test user_membership upgrade SQL has required elements."""
        sql_path = Path(__file__).parent.parent.parent / "alembic" / "sql" / "003_create_user_membership_table_upgrade.sql"
        
        if sql_path.exists():
            content = sql_path.read_text()
            
            # Check for required table elements
            assert "CREATE TABLE IF NOT EXISTS user_membership" in content
            assert "id UUID PRIMARY KEY" in content
            assert "user_id UUID NOT NULL REFERENCES users(id)" in content
            assert "entity_id UUID NOT NULL REFERENCES entity(id)" in content
            assert "role VARCHAR(50)" in content
            assert "ON DELETE CASCADE" in content
            
            # Check for unique constraint
            assert "CONSTRAINT unique_user_entity_membership UNIQUE (user_id, entity_id)" in content
            
            # Check for indexes
            assert "CREATE INDEX idx_user_membership_user_id" in content
            assert "CREATE INDEX idx_user_membership_entity_id" in content
            
            # Check for trigger
            assert "CREATE TRIGGER update_user_membership_updated_at" in content


class TestMigrationIntegration:
    """Integration tests for migrations."""
    
    @pytest.mark.integration
    def test_migration_sequence(self):
        """Test that migrations can be applied in sequence."""
        # This test would run actual migrations against a test database
        pytest.skip("Integration test - requires test database")
    
    @pytest.mark.integration
    def test_migration_rollback(self):
        """Test that migrations can be rolled back."""
        # This test would verify rollback functionality
        pytest.skip("Integration test - requires test database")