Integrations API
================

Base path: ``/accounts/{account_id}/integrations``

The integrations API manages external integrations and logging.

Key Endpoints
-------------

- **GET /accounts/{account_id}/integrations** – List integrations for an account.
- **POST /accounts/{account_id}/integrations** – Create a new integration configuration.
- **GET /accounts/{account_id}/integrations/{integration_id}** – Get details for an integration.
- **PATCH /accounts/{account_id}/integrations/{integration_id}** – Update integration settings.
- **DELETE /accounts/{account_id}/integrations/{integration_id}** – Delete an integration.
- **GET /accounts/{account_id}/integrations/logs** – Retrieve integration execution logs (if enabled).

Cloud Storage Integrations
--------------------------

- Integrations can include cloud storage targets such as Azure, SharePoint, or S3.
- Credentials are stored encrypted and validated when configurations are created or updated.



