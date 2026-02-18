"""add_custom_tone_to_agents

Revision ID: add_custom_tone_agents
Revises: f63e2e56f9b7
Create Date: 2026-02-12 23:26:14.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_custom_tone_agents'
down_revision: Union[str, Sequence[str], None] = 'f63e2e56f9b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add custom tone columns to agents table
    op.add_column('agents', sa.Column('custom_tone_schema_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agents', sa.Column('custom_tone_rows_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agents', sa.Column('custom_tone_schema', sa.Text(), nullable=True))
    op.add_column('agents', sa.Column('custom_tone_rows', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove custom tone columns from agents table
    op.drop_column('agents', 'custom_tone_rows')
    op.drop_column('agents', 'custom_tone_schema')
    op.drop_column('agents', 'custom_tone_rows_enabled')
    op.drop_column('agents', 'custom_tone_schema_enabled')





