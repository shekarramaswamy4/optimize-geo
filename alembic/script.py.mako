"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
import os
from typing import Sequence, Union
from pathlib import Path

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


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
    # TODO: Replace with your SQL file name
    # Example: sql = read_sql_file("001_create_users_table_upgrade.sql")
    # op.execute(sql)
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Downgrade schema using raw SQL file."""
    # TODO: Replace with your SQL file name
    # Example: sql = read_sql_file("001_create_users_table_downgrade.sql")
    # op.execute(sql)
    ${downgrades if downgrades else "pass"}
