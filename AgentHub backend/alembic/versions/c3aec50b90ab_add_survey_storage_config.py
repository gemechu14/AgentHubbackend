"""add_survey_storage_config

Revision ID: c3aec50b90ab
Revises: a964a3b6aadb
Create Date: 2026-01-01 16:49:15.747264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3aec50b90ab'
down_revision: Union[str, Sequence[str], None] = 'a964a3b6aadb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add storage_type and storage_config to surveys table."""
    
    # Create storage type enum (if it doesn't exist)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE storagetype AS ENUM ('DATABASE', 'AZURE', 'SHAREPOINT', 'S3');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Check if columns already exist before adding
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('storage_type', 'storage_config')
    """))
    existing_columns = [row[0] for row in result]
    
    # Add storage_type column with default DATABASE (if it doesn't exist)
    if 'storage_type' not in existing_columns:
        op.add_column('surveys', sa.Column('storage_type', sa.Enum('DATABASE', 'AZURE', 'SHAREPOINT', 'S3', name='storagetype'), nullable=False, server_default='DATABASE'))
    
    # Add storage_config JSONB column (if it doesn't exist)
    if 'storage_config' not in existing_columns:
        op.add_column('surveys', sa.Column('storage_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove storage_type and storage_config from surveys table."""
    
    # Check if columns exist before dropping
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('storage_type', 'storage_config')
    """))
    existing_columns = [row[0] for row in result]
    
    # Remove columns (if they exist)
    if 'storage_config' in existing_columns:
        op.drop_column('surveys', 'storage_config')
    if 'storage_type' in existing_columns:
        op.drop_column('surveys', 'storage_type')
    
    # Drop enum type (if it exists)
    op.execute("""
        DO $$ BEGIN
            DROP TYPE storagetype;
        EXCEPTION
            WHEN undefined_object THEN null;
        END $$;
    """)
