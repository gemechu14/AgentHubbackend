"""add_unique_constraint_agent_id_to_agent_credentials

Revision ID: 67e1957a5dc2
Revises: d200e3a8a4bf
Create Date: 2026-02-18 15:19:21.686787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67e1957a5dc2'
down_revision: Union[str, Sequence[str], None] = 'd200e3a8a4bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # First, handle any duplicate agent_ids by keeping only the most recent one per agent
    # This is a safety measure in case duplicates exist
    op.execute("""
        DELETE FROM agent_credentials a
        USING agent_credentials b
        WHERE a.agent_id = b.agent_id
        AND a.id < b.id
    """)
    
    # Add unique constraint on agent_id
    op.create_unique_constraint(
        'uq_agent_credentials_agent_id',
        'agent_credentials',
        ['agent_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_constraint(
        'uq_agent_credentials_agent_id',
        'agent_credentials',
        type_='unique'
    )
