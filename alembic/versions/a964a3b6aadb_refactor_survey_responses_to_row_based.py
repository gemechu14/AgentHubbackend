"""refactor_survey_responses_to_row_based

Revision ID: a964a3b6aadb
Revises: 001_add_survey_tables
Create Date: 2025-12-24 15:59:19.981478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a964a3b6aadb'
down_revision: Union[str, Sequence[str], None] = '001_add_survey_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Refactor survey_responses to row-based storage."""
    
    # Drop the unique constraint on invite_id (allows multiple responses per invite)
    op.drop_constraint('uq_survey_responses_invite_id', 'survey_responses', type_='unique')
    
    # Add new columns
    op.add_column('survey_responses', sa.Column('submission_batch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('survey_responses', sa.Column('row_index', sa.Integer(), nullable=True))
    
    # Create indexes for new columns
    op.create_index('ix_survey_responses_submission_batch_id', 'survey_responses', ['submission_batch_id'])
    op.create_index('ix_survey_responses_row_index', 'survey_responses', ['row_index'])
    
    # Create composite index for efficient querying
    op.create_index('ix_survey_responses_batch_row', 'survey_responses', ['submission_batch_id', 'row_index'])
    
    # Migrate existing data: convert columnar format to row-based
    # For existing responses, we'll create a submission_batch_id and convert columnar data to rows
    # This is a data migration that will be handled by application code or a separate script
    # For now, we'll just set default values
    op.execute("""
        UPDATE survey_responses 
        SET submission_batch_id = id,
            row_index = 0
        WHERE submission_batch_id IS NULL
    """)


def downgrade() -> None:
    """Revert to original columnar storage."""
    
    # Drop new indexes
    op.drop_index('ix_survey_responses_batch_row', 'survey_responses')
    op.drop_index('ix_survey_responses_row_index', 'survey_responses')
    op.drop_index('ix_survey_responses_submission_batch_id', 'survey_responses')
    
    # Remove new columns
    op.drop_column('survey_responses', 'row_index')
    op.drop_column('survey_responses', 'submission_batch_id')
    
    # Restore unique constraint
    op.create_unique_constraint('uq_survey_responses_invite_id', 'survey_responses', ['invite_id'])
