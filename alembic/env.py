import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# Optional: load .env
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

# Import app settings and aggregated metadata
from app.core.config import settings
from app.db.model_registry import metadata  # this must import ALL model modules

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = metadata

def _get_url() -> str:
    url = settings.database_url or os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL is not set and settings.database_url is empty.")
    return url

def run_migrations_offline():
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = _get_url()
    connectable = engine_from_config(
        {"url": url},          # <-- use "url" when prefix=""
        prefix="",             # <-- no "sqlalchemy." prefix
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
