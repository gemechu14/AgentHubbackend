"""remove_token_expires_at_from_agent_credentials

Revision ID: 42d26ff05f6b
Revises: dd8a6129c5b2
Create Date: 2026-02-19 01:30:46.999104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42d26ff05f6b'
down_revision: Union[str, Sequence[str], None] = 'dd8a6129c5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop token_expires_at column from agent_credentials table if it exists
    # Check if column exists before dropping (handles case where it might not exist)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'agent_credentials' 
                AND column_name = 'token_expires_at'
            ) THEN
                ALTER TABLE agent_credentials DROP COLUMN token_expires_at;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add token_expires_at column (nullable, can be set later)
    op.add_column('agent_credentials', sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True))
