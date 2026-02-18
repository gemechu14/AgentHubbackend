"""add_agent_credentials_tables

Revision ID: add_agent_credentials
Revises: add_manage_agent_ids
Create Date: 2026-02-12 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_agent_credentials'
down_revision: Union[str, Sequence[str], None] = 'add_manage_agent_ids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create agent_credentials table
    op.create_table('agent_credentials',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('client_id', sa.String(length=255), nullable=False),
    sa.Column('client_secret', sa.String(length=255), nullable=False),
    sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_credentials_agent_id'), 'agent_credentials', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_credentials_account_id'), 'agent_credentials', ['account_id'], unique=False)
    op.create_index(op.f('ix_agent_credentials_client_id'), 'agent_credentials', ['client_id'], unique=True)
    
    # Create agent_launch_tokens table
    op.create_table('agent_launch_tokens',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('credential_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['credential_id'], ['agent_credentials.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_launch_tokens_agent_id'), 'agent_launch_tokens', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_launch_tokens_token_hash'), 'agent_launch_tokens', ['token_hash'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop agent_launch_tokens table first (due to foreign key)
    op.drop_index(op.f('ix_agent_launch_tokens_token_hash'), table_name='agent_launch_tokens')
    op.drop_index(op.f('ix_agent_launch_tokens_agent_id'), table_name='agent_launch_tokens')
    op.drop_table('agent_launch_tokens')
    
    # Drop agent_credentials table
    op.drop_index(op.f('ix_agent_credentials_client_id'), table_name='agent_credentials')
    op.drop_index(op.f('ix_agent_credentials_account_id'), table_name='agent_credentials')
    op.drop_index(op.f('ix_agent_credentials_agent_id'), table_name='agent_credentials')
    op.drop_table('agent_credentials')






