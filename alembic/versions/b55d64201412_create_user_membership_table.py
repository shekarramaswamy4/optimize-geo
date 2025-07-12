"""create_user_membership_table

Revision ID: b55d64201412
Revises: 0398f0f9a348
Create Date: 2025-07-13 01:59:51.516602

"""
import os
from typing import Sequence, Union
from pathlib import Path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b55d64201412'
down_revision: Union[str, Sequence[str], None] = '0398f0f9a348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def read_sql_file(filename: str) -> str:
    """Read SQL file from alembic/sql directory."""
    sql_dir = Path(__file__).parent.parent / "sql"
    sql_path = sql_dir / filename
    
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    
    with open(sql_path, "r") as f:
        return f.read()


def upgrade() -> None:
    """Upgrade schema using raw SQL file."""
    sql = read_sql_file("003_create_user_membership_table_upgrade.sql")
    op.execute(sql)


def downgrade() -> None:
    """Downgrade schema using raw SQL file."""
    sql = read_sql_file("003_create_user_membership_table_downgrade.sql")
    op.execute(sql)
