# Quick Migration Steps for Agents Table

## Step-by-Step Instructions

### 1. Verify Model Registration

First, ensure the Agent model is registered in `app/db/model_registry.py`:

```python
from app.models import agent  # noqa
```

✅ Already done - the model is registered.

### 2. Create the Migration

Run this command in your terminal:

```bash
alembic revision --autogenerate -m "add_agents_table"
```

This will create a new migration file in `alembic/versions/` directory.

### 3. Review the Generated Migration

Open the newly created migration file (it will have a name like `xxxxx_add_agents_table.py`) and verify it includes:

- ✅ Table name: `agents`
- ✅ All columns from the Agent model
- ✅ Foreign keys to `accounts` and `users` tables
- ✅ Enum type for `connection_type` (POWERBI, DB)
- ✅ Indexes on `account_id` and `created_by`

### 4. Apply the Migration

Once you've reviewed the migration file, apply it:

```bash
alembic upgrade head
```

### 5. Verify the Migration

Check that the migration was applied successfully:

```bash
# Check current revision
alembic current

# Verify table exists (connect to your database)
psql -U your_user -d your_database -c "\d agents"
```

## Quick Commands Reference

```bash
# Create migration
alembic revision --autogenerate -m "add_agents_table"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1

# Check status
alembic current

# View history
alembic history
```

## Expected Migration File Structure

The migration should create:

1. **Enum Type:**
   ```sql
   CREATE TYPE connectiontype AS ENUM ('POWERBI', 'DB');
   ```

2. **Table:**
   - `agents` with all required columns
   - Foreign keys to `accounts.id` and `users.id`
   - Indexes on foreign key columns

3. **Constraints:**
   - Primary key on `id`
   - Foreign key constraints with CASCADE/SET NULL as defined

## Troubleshooting

### If migration fails with "enum already exists":
The enum might have been created before. Edit the migration file to use:
```python
op.execute("""
    DO $$ BEGIN
        CREATE TYPE connectiontype AS ENUM ('POWERBI', 'DB');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
""")
```

### If foreign key errors occur:
Ensure `accounts` and `users` tables exist. Check migration order.

## After Migration

1. ✅ Test API endpoints in Swagger: `/gibberish-xyz-123`
2. ✅ Create a test agent via POST `/agents/{account_id}`
3. ✅ Verify data is stored correctly

---

For detailed documentation, see: `docs/migration-guide-agents.md`









