"""add_migration_response_count_to_surveys

Revision ID: 480e373036ac
Revises: 2c1453a5fcad
Create Date: 2026-01-22 13:32:05.491880

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '480e373036ac'
down_revision: Union[str, Sequence[str], None] = '2c1453a5fcad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add migration_response_count column to surveys table."""
    
    # Check if column already exists
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name = 'migration_response_count'
    """))
    existing_columns = [row[0] for row in result]
    
    # Add migration_response_count integer column (if it doesn't exist)
    if 'migration_response_count' not in existing_columns:
        op.add_column('surveys', sa.Column('migration_response_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove migration_response_count column from surveys table."""
    
    # Check if column exists before dropping
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name = 'migration_response_count'
    """))
    existing_columns = [row[0] for row in result]
    
    # Remove column (if it exists)
    if 'migration_response_count' in existing_columns:
        op.drop_column('surveys', 'migration_response_count')
