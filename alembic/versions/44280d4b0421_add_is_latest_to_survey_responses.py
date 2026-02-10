"""add_is_latest_to_survey_responses

Revision ID: 44280d4b0421
Revises: f8a9b7c6d5e4
Create Date: 2026-01-15 15:53:48.688002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44280d4b0421'
down_revision: Union[str, Sequence[str], None] = 'f8a9b7c6d5e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
