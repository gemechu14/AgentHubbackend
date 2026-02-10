Accounts API
============

Base path: ``/accounts``

The accounts API manages organizations/accounts and their members.

Key Endpoints
-------------

- **GET /accounts** – List accounts visible to the current user.
- **GET /accounts/{account_id}** – Retrieve details for a specific account.
- **POST /accounts** – Create a new account (typically OWNER-only).
- **PATCH /accounts/{account_id}** – Update account metadata/settings.
- **GET /accounts/{account_id}/members** – List members and their roles.
- **POST /accounts/{account_id}/members** – Add a member to the account.
- **PATCH /accounts/{account_id}/members/{member_id}** – Update member role or status.
- **DELETE /accounts/{account_id}/members/{member_id}** – Remove a member.

Authorization
-------------

- Account-level operations generally require at least **ADMIN** or **OWNER** role.
- Membership listing and some read operations may be available to **MEMBER** or **VIEWER**
  depending on the route.



