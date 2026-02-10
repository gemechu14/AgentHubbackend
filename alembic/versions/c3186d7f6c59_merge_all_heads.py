"""merge_all_heads

Revision ID: c3186d7f6c59
Revises: 001_initial_auth, 1eebd5520f1f, 480e373036ac
Create Date: 2026-02-06 13:50:04.399808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3186d7f6c59'
down_revision: Union[str, Sequence[str], None] = ('001_initial_auth', '1eebd5520f1f', '480e373036ac')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
