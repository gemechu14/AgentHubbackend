# Database Migration Guide - Chat Tables

This guide explains how to create and apply the database migration for the Chat and ChatMessage tables.

## Current Status

✅ **Chat model is already registered** in `app/db/model_registry.py`

❌ **Migration does NOT exist yet** - You need to create it

## Prerequisites

1. Ensure your database connection is configured in `.env` or environment variables:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

2. Make sure you have Alembic installed (should already be in requirements.txt):
   ```bash
   pip install alembic
   ```

## Step 1: Verify Model Registration

The chat model should already be registered. Verify by checking `app/db/model_registry.py`:

```python
from app.models import chat  # noqa
```

✅ This is already done.

## Step 2: Create the Migration

Run the following command to auto-generate a migration file based on your Chat and ChatMessage models:

```bash
alembic revision --autogenerate -m "add_chat_and_chat_message_tables"
```

This will:
- Detect the new `Chat` and `ChatMessage` models from `app/models/chat.py`
- Generate a migration file in `alembic/versions/`
- Create the migration with the appropriate table structure

## Step 3: Review the Generated Migration

The migration file will be created in `alembic/versions/` with a name like:
```
<revision_id>_add_chat_and_chat_message_tables.py
```

**Important:** Review the generated migration file before applying it. It should include:

### Chat Table:
- Table name: `chats`
- Columns:
  - `id` (UUID, primary key)
  - `title` (String(255), default: "New Chat")
  - `agent_id` (UUID, ForeignKey to agents.id, CASCADE on delete, indexed)
  - `user_id` (UUID, ForeignKey to users.id, CASCADE on delete, indexed)
  - `account_id` (UUID, ForeignKey to accounts.id, CASCADE on delete, indexed)
  - `created_at` (DateTime with timezone, server default: now())
  - `updated_at` (DateTime with timezone, server default: now())
- Foreign key constraints
- Indexes on `agent_id`, `user_id`, and `account_id`

### ChatMessage Table:
- Table name: `chat_messages`
- Columns:
  - `id` (UUID, primary key)
  - `chat_id` (UUID, ForeignKey to chats.id, CASCADE on delete, indexed)
  - `role` (String(20), not null) - "user" or "assistant"
  - `content` (Text, not null)
  - `action` (String(50), nullable) - "DESCRIBE", "QUERY", "ERROR"
  - `dax_attempts` (Text, nullable) - JSON string array
  - `final_dax` (Text, nullable)
  - `resolution_note` (Text, nullable)
  - `error` (Text, nullable)
  - `created_at` (DateTime with timezone, server default: now())
- Foreign key constraint to `chats.id` with CASCADE on delete
- Index on `chat_id`

### Expected Migration Structure

The generated migration should look similar to this:

```python
"""add_chat_and_chat_message_tables

Revision ID: <revision_id>
Revises: 779affdda697
Create Date: <timestamp>

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '<revision_id>'
down_revision = '779affdda697'  # Should reference the agents table migration
branch_labels = None
depends_on = None

def upgrade():
    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Chat'),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chats_agent_id'), 'chats', ['agent_id'], unique=False)
    op.create_index(op.f('ix_chats_user_id'), 'chats', ['user_id'], unique=False)
    op.create_index(op.f('ix_chats_account_id'), 'chats', ['account_id'], unique=False)
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=True),
        sa.Column('dax_attempts', sa.Text(), nullable=True),
        sa.Column('final_dax', sa.Text(), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_chat_id'), 'chat_messages', ['chat_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_chat_messages_chat_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index(op.f('ix_chats_account_id'), table_name='chats')
    op.drop_index(op.f('ix_chats_user_id'), table_name='chats')
    op.drop_index(op.f('ix_chats_agent_id'), table_name='chats')
    op.drop_table('chats')
```

## Step 4: Apply the Migration

Once you've reviewed the migration file and it looks correct, apply it:

```bash
alembic upgrade head
```

This will:
- Create the `chats` table
- Create the `chat_messages` table
- Set up all foreign keys and indexes

## Step 5: Verify the Migration

Check that the migration was applied successfully:

```bash
# Check current revision
alembic current

# View migration history
alembic history

# Verify tables exist (connect to your database)
psql -U your_user -d your_database -c "\d chats"
psql -U your_user -d your_database -c "\d chat_messages"
```

Or using Python:
```python
from app.db.session import SessionLocal
from sqlalchemy import inspect

db = SessionLocal()
inspector = inspect(db.bind)

# Check if tables exist
print("chats" in inspector.get_table_names())
print("chat_messages" in inspector.get_table_names())
```

## Quick Commands Reference

```bash
# Create migration
alembic revision --autogenerate -m "add_chat_and_chat_message_tables"

# Apply migration
alembic upgrade head

# Rollback if needed (removes the tables)
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history

# Show SQL that would be executed (without applying)
alembic upgrade head --sql
```

## Troubleshooting

### Issue: Migration doesn't detect the chat tables

**Solution:** 
1. Verify `app/models/chat.py` exists and has the models
2. Verify `app/db/model_registry.py` imports the chat module:
   ```python
   from app.models import chat  # noqa
   ```
3. Make sure you're running the command from the project root directory

### Issue: "Table already exists" error

**Solution:** 
- The tables might have been created manually. Check your database:
  ```sql
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public' AND table_name IN ('chats', 'chat_messages');
  ```
- If tables exist but migration doesn't, you may need to mark the migration as applied:
  ```bash
  alembic stamp head
  ```

### Issue: Foreign key constraint errors

**Solution:**
- Ensure the `agents`, `users`, and `accounts` tables exist
- Check that the referenced columns have the correct UUID type
- Verify the `agents` table migration was applied first

### Issue: Migration fails with "enum already exists"

**Solution:**
- This shouldn't happen for chat tables (no enums), but if you see this, the enum might already exist from a previous migration

## What Gets Created

After running the migration, you'll have:

1. **`chats` table** with:
   - Primary key: `id` (UUID)
   - Foreign keys to: `agents`, `users`, `accounts`
   - Indexes on all foreign key columns
   - Timestamps: `created_at`, `updated_at`

2. **`chat_messages` table** with:
   - Primary key: `id` (UUID)
   - Foreign key to: `chats` (CASCADE delete)
   - Index on `chat_id`
   - Message content and metadata fields
   - Timestamp: `created_at`

3. **Cascade behavior:**
   - Deleting an agent → deletes all its chats → deletes all messages
   - Deleting a user → deletes all their chats → deletes all messages
   - Deleting an account → deletes all its chats → deletes all messages
   - Deleting a chat → deletes all its messages

## Next Steps

After the migration is applied:

1. ✅ Tables are created
2. ✅ API endpoints are ready (`/chats/*`)
3. ✅ You can start using the chat system

Test the API:
```bash
# Create a chat
POST /chats/{account_id}/{agent_id}
{
  "title": "Test Chat"
}

# Send a message
POST /chats/{account_id}/{agent_id}/{chat_id}/messages
{
  "content": "Hello!"
}
```

## Rollback (if needed)

If you need to rollback the migration:

```bash
alembic downgrade -1
```

This will:
- Drop the `chat_messages` table
- Drop the `chats` table
- Remove all indexes

**Warning:** This will delete all chat data! Only use this in development or if you have backups.






