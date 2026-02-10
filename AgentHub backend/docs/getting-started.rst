Getting Started
================

This guide will help you get started with the SmartSchema Backend API.

Prerequisites
-------------

- Python 3.9+ (recommended: Python 3.10 or higher)
- PostgreSQL database
- pip (Python package manager)

Installation
------------

1. Clone the Repository
   ::

      git clone <repository-url>
      cd SmartSchema-Backend

2. Create a Virtual Environment
   
   Windows::
   
      python -m venv venv
      venv\Scripts\activate
   
   macOS/Linux::
   
      python3 -m venv venv
      source venv/bin/activate

3. Install Dependencies
   ::

      pip install -r requirements.txt

   Note: The project uses `python-dotenv` but it's not listed in `requirements.txt`. You may need to install it separately::

      pip install python-dotenv

4. Set Up Environment Variables

   Create a `.env` file in the root directory with the following variables:

   .. code-block:: env

      # Database Configuration
      DATABASE_URL=postgresql://username:password@localhost:5432/smartschema_db

      # Application Settings
      APP_NAME=SmartSchema
      APP_BASE_URL=https://app.smartschema.io

      # JWT Configuration
      JWT_SECRET=your-secret-key-here
      JWT_ISSUER=locimapper-api
      ACCESS_TOKEN_TTL_MIN=15
      REFRESH_TOKEN_TTL_DAYS=30

      # Email Configuration
      SMTP_SERVER=smtp.example.com
      SMTP_PORT=587
      SMTP_USER=your-email@example.com
      SMTP_PASSWORD=your-password
      MAIL_FROM=your-email@example.com
      MAIL_FROM_NAME=SmartSchema

      # Google OAuth (optional)
      GOOGLE_CLIENT_ID=your-google-client-id
      GOOGLE_CLIENT_SECRET=your-google-client-secret
      GOOGLE_REDIRECT_URI=https://app.smartschema.io/auth/google/callback

      # Invitation and Verification Settings
      INVITE_EXP_DAYS=7
      EMAIL_VERIFY_EXP_HOURS=24
      EMAIL_VERIFY_RESEND_COOLDOWN_S=60
      PASSWORD_RESET_EXP_HOURS=24
      LAUNCH_TOKEN_TTL_SECONDS=300

      # Survey Settings
      SURVEY_INVITE_EXP_DAYS=14
      SURVEY_BATCH_SIZE=1000

5. Run Database Migrations
   ::

      alembic upgrade head

6. Start the Development Server
   ::

      uvicorn app.main:app --reload

The API will be available at:
- **Base URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/gibberish-xyz-123

Project Structure
-----------------

::

   SmartSchema-Backend/
   ├── alembic/              # Database migration scripts
   ├── app/
   │   ├── api/              # API routes and dependencies
   │   │   └── routes/       # Route handlers
   │   ├── core/             # Core configuration and security
   │   ├── db/               # Database session and models
   │   ├── models/           # SQLAlchemy models
   │   ├── schemas/          # Pydantic schemas
   │   ├── services/         # Business logic services
   │   └── main.py           # FastAPI application entry point
   ├── migrations/           # Additional migration files
   ├── scripts/              # Utility scripts
   ├── alembic.ini           # Alembic configuration
   ├── requirements.txt      # Python dependencies
   └── vercel.json           # Vercel deployment configuration

