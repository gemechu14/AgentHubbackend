"""add_pipeline_fields

Revision ID: 56c55970b98a
Revises: 9e5b36b1c9c4
Create Date: 2026-01-02 20:05:12.656519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '56c55970b98a'
down_revision: Union[str, Sequence[str], None] = '9e5b36b1c9c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pipeline fields to surveys table."""
    
    # Check if columns already exist
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('pipeline_config', 'pipeline_next_run', 'pipeline_last_run')
    """))
    existing_columns = [row[0] for row in result]
    
    # Add pipeline_config JSONB column (if it doesn't exist)
    if 'pipeline_config' not in existing_columns:
        op.add_column('surveys', sa.Column('pipeline_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add pipeline_next_run timestamp column (if it doesn't exist)
    if 'pipeline_next_run' not in existing_columns:
        op.add_column('surveys', sa.Column('pipeline_next_run', sa.DateTime(timezone=True), nullable=True))
    
    # Add pipeline_last_run timestamp column (if it doesn't exist)
    if 'pipeline_last_run' not in existing_columns:
        op.add_column('surveys', sa.Column('pipeline_last_run', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove pipeline fields from surveys table."""
    
    # Check if columns exist before dropping
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'surveys' 
        AND column_name IN ('pipeline_config', 'pipeline_next_run', 'pipeline_last_run')
    """))
    existing_columns = [row[0] for row in result]
    
    # Remove columns (if they exist)
    if 'pipeline_last_run' in existing_columns:
        op.drop_column('surveys', 'pipeline_last_run')
    if 'pipeline_next_run' in existing_columns:
        op.drop_column('surveys', 'pipeline_next_run')
    if 'pipeline_config' in existing_columns:
        op.drop_column('surveys', 'pipeline_config')
