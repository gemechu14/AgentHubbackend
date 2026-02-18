# Database Migration Guide - Agents Table

This guide explains how to create and apply the database migration for the Agents table.

## Prerequisites

1. Ensure your database connection is configured in `.env` or environment variables:
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

2. Make sure you have Alembic installed:
   ```bash
   pip install alembic
   ```

## Step 1: Create the Migration

Run the following command to auto-generate a migration file based on your Agent model:

```bash
alembic revision --autogenerate -m "add_agents_table"
```

This will:
- Detect the new `Agent` model from `app/models/agent.py`
- Generate a migration file in `alembic/versions/`
- Create the migration with the appropriate table structure

## Step 2: Review the Generated Migration

The migration file will be created in `alembic/versions/` with a name like:
```
<revision_id>_add_agents_table.py
```

**Important:** Review the generated migration file before applying it. It should include:

- Table creation: `agents`
- Columns:
  - `id` (UUID, primary key)
  - `name` (String)
  - `description` (Text, nullable)
  - `status` (String)
  - `model_type` (String, nullable)
  - `api_key` (String, nullable)
  - `system_instructions` (Text, nullable)
  - `connection_type` (Enum: POWERBI, DB)
  - `connection_config` (JSONB)
  - `account_id` (UUID, ForeignKey to accounts.id)
  - `created_by` (UUID, ForeignKey to users.id, nullable)
  - `created_at` (DateTime with timezone)
  - `updated_at` (DateTime with timezone, nullable)
- Foreign key constraints
- Indexes on `account_id` and `created_by`

### Example Migration File Structure

The generated migration should look similar to this:

```python
"""add_agents_table

Revision ID: <revision_id>
Revises: <previous_revision>
Create Date: <timestamp>

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '<revision_id>'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum type for connection_type
    op.execute("CREATE TYPE connectiontype AS ENUM ('POWERBI', 'DB')")
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('model_type', sa.String(length=100), nullable=True),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('system_instructions', sa.Text(), nullable=True),
        sa.Column('connection_type', sa.Enum('POWERBI', 'DB', name='connectiontype'), nullable=False),
        sa.Column('connection_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes
    op.create_index(op.f('ix_agents_account_id'), 'agents', ['account_id'], unique=False)
    op.create_index(op.f('ix_agents_created_by'), 'agents', ['created_by'], unique=False)

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_agents_created_by'), table_name='agents')
    op.drop_index(op.f('ix_agents_account_id'), table_name='agents')
    
    # Drop table
    op.drop_table('agents')
    
    # Drop enum type
    op.execute("DROP TYPE connectiontype")
```

## Step 3: Apply the Migration

Once you've reviewed and confirmed the migration looks correct, apply it to your database:

```bash
alembic upgrade head
```

This will:
- Execute the `upgrade()` function in the migration
- Create the `agents` table in your database
- Set up all constraints, indexes, and foreign keys

## Step 4: Verify the Migration

### Check Migration Status

```bash
alembic current
```

This shows the current database revision.

### Check Migration History

```bash
alembic history
```

This shows all migrations and their order.

### Verify Table Creation

Connect to your database and verify the table was created:

```sql
-- PostgreSQL
\dt agents

-- Or query the table structure
\d agents

-- Or check if table exists
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'agents';
```

## Step 5: Rollback (If Needed)

If you need to rollback the migration:

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations (use with caution!)
alembic downgrade base
```

**Warning:** Rolling back will drop the `agents` table and all its data!

## Troubleshooting

### Issue: Migration not detecting the Agent model

**Solution:** Ensure the Agent model is imported in `app/db/model_registry.py`:

```python
from app.models import agent  # noqa
```

### Issue: Enum type already exists

If you see an error like `type "connectiontype" already exists`, the enum might have been created in a previous migration. You can:

1. **Option 1:** Remove the enum creation from the migration if it already exists
2. **Option 2:** Use `CREATE TYPE IF NOT EXISTS` (PostgreSQL 9.5+)

Modify the migration:

```python
def upgrade() -> None:
    # Check if enum exists before creating
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE connectiontype AS ENUM ('POWERBI', 'DB');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    # ... rest of migration
```

### Issue: Foreign key constraint fails

If you get foreign key errors, ensure:
- The `accounts` table exists
- The `users` table exists
- You're applying migrations in the correct order

### Issue: Database connection error

Check your `DATABASE_URL` environment variable:

```bash
# Check if DATABASE_URL is set
echo $DATABASE_URL

# Or check .env file
cat .env | grep DATABASE_URL
```

## Production Deployment

For production deployments:

1. **Backup your database first:**
   ```bash
   pg_dump -h localhost -U user -d dbname > backup_before_agents_migration.sql
   ```

2. **Test the migration on a staging environment first**

3. **Apply during a maintenance window** (if possible)

4. **Monitor the migration:**
   ```bash
   # Run with verbose output
   alembic upgrade head --sql  # Preview SQL without executing
   alembic upgrade head -v      # Verbose output
   ```

5. **Verify after deployment:**
   ```bash
   alembic current
   ```

## Manual Migration (Alternative)

If auto-generation doesn't work or you prefer manual control, you can create an empty migration:

```bash
alembic revision -m "add_agents_table"
```

Then manually write the `upgrade()` and `downgrade()` functions in the generated file.

## Next Steps

After successfully applying the migration:

1. ✅ Verify the table exists in your database
2. ✅ Test the API endpoints using Swagger UI (`/gibberish-xyz-123`)
3. ✅ Create a test agent via the API
4. ✅ Verify data is stored correctly

## Quick Reference Commands

```bash
# Create migration
alembic revision --autogenerate -m "add_agents_table"

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current revision
alembic current

# View migration history
alembic history

# Show SQL without executing
alembic upgrade head --sql
```









