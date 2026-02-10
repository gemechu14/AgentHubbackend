Auth API
========

Base path: ``/auth``

This section summarizes the primary authentication endpoints. For full request/response
schemas, refer to the interactive docs at ``/gibberish-xyz-123`` on a running instance.

Key Endpoints
-------------

- **POST /auth/register** – Register a new user account.
- **POST /auth/login** – Email/password login, returns access and refresh tokens.
- **POST /auth/refresh** – Exchange a valid refresh token for a new access token.
- **POST /auth/logout** – Invalidate tokens (implementation-specific).
- **POST /auth/password/reset/request** – Request a password reset email.
- **POST /auth/password/reset/confirm** – Confirm password reset with token.
- **POST /auth/email/verify** – Verify email address using verification token.
- **GET /auth/me** – Get current authenticated user profile.

Security
--------

- Most endpoints require a valid ``Authorization: Bearer <access_token>`` header,
  except for registration, login, and public verification/reset endpoints.
- See :doc:`Security & Authentication <security>` for the overall model.



