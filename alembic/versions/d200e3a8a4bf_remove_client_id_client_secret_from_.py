"""remove_client_id_client_secret_from_agent_credentials

Revision ID: d200e3a8a4bf
Revises: add_agent_credentials
Create Date: 2026-02-18 15:14:39.392839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd200e3a8a4bf'
down_revision: Union[str, Sequence[str], None] = 'add_agent_credentials'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make credential_id nullable in agent_launch_tokens
    op.alter_column('agent_launch_tokens', 'credential_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True)
    
    # Drop index on client_id before dropping the column
    op.drop_index('ix_agent_credentials_client_id', table_name='agent_credentials')
    
    # Drop client_id and client_secret columns from agent_credentials
    op.drop_column('agent_credentials', 'client_secret')
    op.drop_column('agent_credentials', 'client_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add client_id and client_secret columns to agent_credentials
    op.add_column('agent_credentials', sa.Column('client_id', sa.String(length=255), nullable=False))
    op.add_column('agent_credentials', sa.Column('client_secret', sa.String(length=255), nullable=False))
    
    # Re-create index on client_id
    op.create_index('ix_agent_credentials_client_id', 'agent_credentials', ['client_id'], unique=True)
    
    # Make credential_id non-nullable again in agent_launch_tokens
    op.alter_column('agent_launch_tokens', 'credential_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=False)
