"""add_azure_blob_storage_type

Revision ID: f8a9b7c6d5e4
Revises: 56c55970b98a
Create Date: 2026-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a9b7c6d5e4'
down_revision: Union[str, Sequence[str], None] = '56c55970b98a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AZURE_BLOB to storagetype enum."""
    
    # Add AZURE_BLOB to the existing enum type
    # PostgreSQL doesn't support adding enum values in a transaction easily,
    # so we use ALTER TYPE ... ADD VALUE which commits immediately
    op.execute("""
        DO $$ BEGIN
            ALTER TYPE storagetype ADD VALUE IF NOT EXISTS 'AZURE_BLOB';
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade() -> None:
    """Remove AZURE_BLOB from storagetype enum."""
    
    # Note: PostgreSQL doesn't support removing enum values directly.
    # This would require recreating the enum type and updating all columns.
    # For safety, we'll leave the enum value in place.
    # If you need to remove it, you would need to:
    # 1. Create a new enum without AZURE_BLOB
    # 2. Alter the column to use the new enum
    # 3. Drop the old enum
    # 4. Rename the new enum to the old name
    # This is complex and risky, so we skip it for now.
    pass
















