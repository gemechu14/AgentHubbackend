# Quick Migration Steps for Chat Tables

## ✅ Current Status

- ✅ Chat model is registered in `app/db/model_registry.py`
- ❌ Migration does NOT exist yet - **You need to create it**

## Step-by-Step Instructions

### Step 1: Create the Migration

Run this command in your terminal (from project root):

```bash
alembic revision --autogenerate -m "add_chat_and_chat_message_tables"
```

This will create a new migration file in `alembic/versions/` directory.

### Step 2: Review the Generated Migration

Open the newly created migration file (it will have a name like `xxxxx_add_chat_and_chat_message_tables.py`) and verify it includes:

- ✅ Table: `chats` with all required columns
- ✅ Table: `chat_messages` with all required columns
- ✅ Foreign keys to `agents`, `users`, and `accounts` tables
- ✅ Indexes on foreign key columns
- ✅ CASCADE delete behavior

### Step 3: Apply the Migration

Once you've reviewed the migration file, apply it:

```bash
alembic upgrade head
```

### Step 4: Verify the Migration

Check that the migration was applied successfully:

```bash
# Check current revision
alembic current

# Verify tables exist (if you have psql)
psql -U your_user -d your_database -c "\d chats"
psql -U your_user -d your_database -c "\d chat_messages"
```

## Quick Commands Reference

```bash
# Create migration
alembic revision --autogenerate -m "add_chat_and_chat_message_tables"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1

# Check status
alembic current

# View history
alembic history
```

## What Gets Created

After running the migration, you'll have:

1. **`chats` table** - Stores chat conversations
2. **`chat_messages` table** - Stores individual messages

Both tables will have proper foreign keys, indexes, and cascade delete behavior.

## Troubleshooting

### If migration doesn't detect the tables:
- Verify `app/models/chat.py` exists
- Verify `app/db/model_registry.py` has: `from app.models import chat  # noqa`

### If you get foreign key errors:
- Make sure the `agents` table migration was applied first
- Run `alembic current` to check migration status

For more details, see `docs/migration-guide-chat.md`









