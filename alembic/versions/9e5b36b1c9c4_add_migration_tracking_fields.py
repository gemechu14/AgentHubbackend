"""add_migration_tracking_fields

Revision ID: 9e5b36b1c9c4
Revises: c3aec50b90ab
Create Date: 2026-01-02 18:08:37.563762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e5b36b1c9c4'
down_revision: Union[str, Sequence[str], None] = 'c3aec50b90ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add migration tracking fields to surveys table."""
    
    # Check if columns already exist
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('previous_storage_type', 'is_migrated', 'migrated_at', 'migrated_count')
    """))
    existing_columns = [row[0] for row in result]
    
    # Add previous_storage_type column (if it doesn't exist)
    if 'previous_storage_type' not in existing_columns:
        op.add_column('surveys', sa.Column('previous_storage_type', sa.Enum('DATABASE', 'AZURE', 'SHAREPOINT', 'S3', name='storagetype'), nullable=True))
    
    # Add is_migrated boolean column (if it doesn't exist)
    if 'is_migrated' not in existing_columns:
        op.add_column('surveys', sa.Column('is_migrated', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add migrated_at timestamp column (if it doesn't exist)
    if 'migrated_at' not in existing_columns:
        op.add_column('surveys', sa.Column('migrated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add migrated_count integer column (if it doesn't exist)
    if 'migrated_count' not in existing_columns:
        op.add_column('surveys', sa.Column('migrated_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove migration tracking fields from surveys table."""
    
    # Check if columns exist before dropping
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('previous_storage_type', 'is_migrated', 'migrated_at', 'migrated_count')
    """))
    existing_columns = [row[0] for row in result]
    
    # Remove columns (if they exist)
    if 'migrated_count' in existing_columns:
        op.drop_column('surveys', 'migrated_count')
    if 'migrated_at' in existing_columns:
        op.drop_column('surveys', 'migrated_at')
    if 'is_migrated' in existing_columns:
        op.drop_column('surveys', 'is_migrated')
    if 'previous_storage_type' in existing_columns:
        op.drop_column('surveys', 'previous_storage_type')
