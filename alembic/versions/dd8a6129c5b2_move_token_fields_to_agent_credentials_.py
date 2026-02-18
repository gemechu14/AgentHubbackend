"""move_token_fields_to_agent_credentials_and_drop_launch_tokens_table

Revision ID: dd8a6129c5b2
Revises: 5d2b9a3d1267
Create Date: 2026-02-19 01:22:22.559495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd8a6129c5b2'
down_revision: Union[str, Sequence[str], None] = '5d2b9a3d1267'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy.dialects import postgresql
    
    # 1. Add token fields to agent_credentials table
    op.add_column('agent_credentials', sa.Column('token_hash', sa.String(length=128), nullable=True))
    op.add_column('agent_credentials', sa.Column('raw_token', sa.String(length=200), nullable=True))
    
    # 2. Create index on token_hash for faster lookups
    op.create_index(op.f('ix_agent_credentials_token_hash'), 'agent_credentials', ['token_hash'], unique=False)
    
    # 3. Migrate data from agent_launch_tokens to agent_credentials
    # For each credential, get the most recent token and update the credential
    op.execute("""
        UPDATE agent_credentials ac
        SET 
            token_hash = (
                SELECT alt.token_hash 
                FROM agent_launch_tokens alt 
                WHERE alt.agent_id = ac.agent_id 
                ORDER BY alt.created_at DESC 
                LIMIT 1
            ),
            raw_token = (
                SELECT alt.raw_token 
                FROM agent_launch_tokens alt 
                WHERE alt.agent_id = ac.agent_id 
                ORDER BY alt.created_at DESC 
                LIMIT 1
            )
        WHERE EXISTS (
            SELECT 1 
            FROM agent_launch_tokens alt 
            WHERE alt.agent_id = ac.agent_id 
        )
    """)
    
    # 4. Drop indexes on agent_launch_tokens
    op.drop_index(op.f('ix_agent_launch_tokens_token_hash'), table_name='agent_launch_tokens')
    op.drop_index(op.f('ix_agent_launch_tokens_agent_id'), table_name='agent_launch_tokens')
    
    # 5. Drop agent_launch_tokens table
    op.drop_table('agent_launch_tokens')


def downgrade() -> None:
    """Downgrade schema."""
    from sqlalchemy.dialects import postgresql
    
    # 1. Recreate agent_launch_tokens table
    op.create_table('agent_launch_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('raw_token', sa.String(length=200), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['credential_id'], ['agent_credentials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_launch_tokens_agent_id'), 'agent_launch_tokens', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_launch_tokens_token_hash'), 'agent_launch_tokens', ['token_hash'], unique=True)
    
    # 2. Migrate data back from agent_credentials to agent_launch_tokens
    op.execute("""
        INSERT INTO agent_launch_tokens (id, agent_id, token_hash, raw_token, expires_at, created_at)
        SELECT 
            gen_random_uuid(),
            ac.agent_id,
            ac.token_hash,
            ac.raw_token,
            NOW() + INTERVAL '5 minutes',  -- Default expiration for downgrade
            NOW()
        FROM agent_credentials ac
        WHERE ac.token_hash IS NOT NULL
    """)
    
    # 3. Drop index and columns from agent_credentials
    op.drop_index(op.f('ix_agent_credentials_token_hash'), table_name='agent_credentials')
    op.drop_column('agent_credentials', 'raw_token')
    op.drop_column('agent_credentials', 'token_hash')
