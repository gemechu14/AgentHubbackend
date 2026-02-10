Configuration
=============

Environment Variables
---------------------

The SmartSchema Backend uses environment variables for configuration. All settings are loaded from a `.env` file in the root directory.

Database Configuration
~~~~~~~~~~~~~~~~~~~~~

.. envvar:: DATABASE_URL

   PostgreSQL database connection string.
   
   Format: ``postgresql://username:password@host:port/database``
   
   Example: ``postgresql://user:pass@localhost:5432/smartschema_db``

Application Settings
~~~~~~~~~~~~~~~~~~~~

.. envvar:: APP_NAME

   Application name (default: "SmartSchema")

.. envvar:: APP_BASE_URL

   Base URL for the application frontend (default: "https://app.smartschema.io")

JWT Configuration
~~~~~~~~~~~~~~~~~

.. envvar:: JWT_SECRET

   Secret key for JWT token signing (required, default: "change-me")

.. envvar:: JWT_ISSUER

   JWT issuer identifier (default: "locimapper-api")

.. envvar:: ACCESS_TOKEN_TTL_MIN

   Access token time-to-live in minutes (default: 15)

.. envvar:: REFRESH_TOKEN_TTL_DAYS

   Refresh token time-to-live in days (default: 30)

Email Configuration
~~~~~~~~~~~~~~~~~~~

.. envvar:: SMTP_SERVER

   SMTP server hostname

.. envvar:: SMTP_PORT

   SMTP server port (default: 587)

.. envvar:: SMTP_USER

   SMTP authentication username

.. envvar:: SMTP_PASSWORD

   SMTP authentication password

.. envvar:: MAIL_FROM

   Email address to send emails from

.. envvar:: MAIL_FROM_NAME

   Display name for email sender (default: "SmartSchema")

Google OAuth Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: GOOGLE_CLIENT_ID

   Google OAuth client ID

.. envvar:: GOOGLE_CLIENT_SECRET

   Google OAuth client secret

.. envvar:: GOOGLE_REDIRECT_URI

   Google OAuth redirect URI

Invitation and Verification Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. envvar:: INVITE_EXP_DAYS

   Invitation expiration in days (default: 7)

.. envvar:: EMAIL_VERIFY_EXP_HOURS

   Email verification link expiration in hours (default: 24)

.. envvar:: EMAIL_VERIFY_RESEND_COOLDOWN_S

   Cooldown in seconds before allowing another verification email to be resent (default: 60)

.. envvar:: PASSWORD_RESET_EXP_HOURS

   Password reset link expiration in hours (default: 24)

.. envvar:: LAUNCH_TOKEN_TTL_SECONDS

   Launch token TTL in seconds for standalone import page tokens (default: 300)

Survey Settings
~~~~~~~~~~~~~~~

.. envvar:: SURVEY_INVITE_EXP_DAYS

   Survey invitation expiration in days (default: 14)

.. envvar:: SURVEY_BATCH_SIZE

   Survey batch processing size (default: 1000)

CORS Configuration
------------------

The application is configured to allow requests from:

- ``https://app.smartschema.io``
- ``https://www.app.smartschema.io``
- ``http://localhost:3000`` (for local development)
- ``http://localhost:3001`` (for local development)
- ``https://smartschema.io``
- ``https://www.smartschema.io``

CORS settings can be updated in ``app/main.py``.

Database Migrations
-------------------

The project uses Alembic for database migrations.

Create a new migration::

   alembic revision --autogenerate -m "description of changes"

Apply migrations::

   alembic upgrade head

Rollback migration::

   alembic downgrade -1

