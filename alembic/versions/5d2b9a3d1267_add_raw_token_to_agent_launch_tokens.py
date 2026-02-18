"""add_raw_token_to_agent_launch_tokens

Revision ID: 5d2b9a3d1267
Revises: 67e1957a5dc2
Create Date: 2026-02-19 00:29:37.069008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d2b9a3d1267'
down_revision: Union[str, Sequence[str], None] = '67e1957a5dc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add raw_token column to agent_launch_tokens table
    op.add_column(
        'agent_launch_tokens',
        sa.Column('raw_token', sa.String(length=200), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove raw_token column from agent_launch_tokens table
    op.drop_column('agent_launch_tokens', 'raw_token')
