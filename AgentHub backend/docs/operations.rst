Operations & Deployment
=======================

This section covers how to run, deploy, and operate the SmartSchema backend in different environments.

Environments
------------

Typical environments:

- **local** – developer workstation, using ``uvicorn`` with ``--reload``.
- **staging** – pre-production environment mirroring production configuration as closely as possible.
- **production** – highly available deployment with proper monitoring and backups.

Running Locally
---------------

For local development:

1. Apply database migrations:

   .. code-block:: bash

      alembic upgrade head

2. Start the API:

   .. code-block:: bash

      uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. Verify health and docs:

   - Health check: ``GET /health``
   - API docs (Swagger): ``/gibberish-xyz-123``

Database Migrations
-------------------

SmartSchema uses Alembic for schema migrations.

- Create migration:

  .. code-block:: bash

     alembic revision --autogenerate -m "description of changes"

- Apply migrations:

  .. code-block:: bash

     alembic upgrade head

- Roll back:

  .. code-block:: bash

     alembic downgrade -1

For complex recovery scenarios, see the root-level ``restore_database.md`` guide.

Configuration Management
------------------------

Configuration is provided via environment variables (usually through a ``.env`` file in non-production).
Production environments should inject configuration via the process environment or a secrets manager.

See :doc:`Configuration <configuration>` for the full list of supported settings.

Monitoring & Health
-------------------

At minimum, production deployments should:

- Monitor the ``/health`` endpoint for liveness.
- Collect logs from the application process and database.
- Track error rates and latencies for key endpoints (authentication, surveys, and webhooks).

Backups & Recovery
------------------

Because the system depends heavily on PostgreSQL, regular database backups are essential:

- Use your cloud provider's managed backups or scheduled dump (e.g., ``pg_dump``).
- Test restore procedures regularly using a staging environment.




