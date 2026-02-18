"""add_manage_agent_ids_to_invitations_memberships

Revision ID: add_manage_agent_ids
Revises: add_custom_tone_agents
Create Date: 2026-02-12 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_manage_agent_ids'
down_revision: Union[str, Sequence[str], None] = 'add_custom_tone_agents'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add manage_agent_ids column to memberships table
    op.add_column('memberships', sa.Column('manage_agent_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add manage_agent_ids column to invitations table
    op.add_column('invitations', sa.Column('manage_agent_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove manage_agent_ids columns
    op.drop_column('invitations', 'manage_agent_ids')
    op.drop_column('memberships', 'manage_agent_ids')








