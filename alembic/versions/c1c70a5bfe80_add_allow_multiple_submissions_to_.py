"""add_allow_multiple_submissions_to_surveys

Revision ID: c1c70a5bfe80
Revises: 44280d4b0421
Create Date: 2026-01-15 16:03:30.353346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1c70a5bfe80'
down_revision: Union[str, Sequence[str], None] = '44280d4b0421'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
