"""add_recommended_questions_to_agents

Revision ID: add_recommended_questions
Revises: add_custom_tone_agents
Create Date: 2026-01-XX XX:XX:XX.XXXXXX

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'add_recommended_questions'
down_revision: Union[str, Sequence[str], None] = '42d26ff05f6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add recommended_questions column to agents table (stored as JSONB array)
    op.add_column('agents', sa.Column('recommended_questions', JSONB(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove recommended_questions column from agents table
    op.drop_column('agents', 'recommended_questions')

