# Changelog — Recent Updates (May 2026)

This document summarizes the code and UI updates made recently so they are discoverable for operators and developers.

## Summary of Changes

- Authentication
  - Added `services/auth_service.py` implementing bcrypt hashing, in-memory session tokens, and helpers for login/logout/validate/change-password.
  - Added an auth router `backend/api/auth_router.py` exposing `POST /auth/login`, `POST /auth/logout`, `GET /auth/validate`, and `POST /auth/change-password`.

- API updates
  - Protected write operations with a token validation helper; the helper is used by endpoints performing mutations (company creation, license renew/suspend).
  - `POST /api/companies` now prevents duplicate enterprises by checking registration number and company name before creating a new record.
  - Added `POST /api/licenses/{id}/renew` and `POST /api/licenses/{id}/suspend` to support runtime license management.

- Frontend
  - `frontend/js/main_dashboard_controller.js` updated: the Add Contract flow now uses a combo/select for `company_address`; a Change Password form was added to Settings.
  - `frontend/js/frontend_api_client.js` updated to accept and forward `Authorization` tokens returned by the auth endpoints.

- Misc
  - `requirements.txt` updated to include `bcrypt`.
  - Admin bootstrap: the backend ensures a default admin user exists on startup to allow first-time login.

## Files Touched

- Backend code
  - [services/auth_service.py](services/auth_service.py)
  - [backend/api/auth_router.py](backend/api/auth_router.py)
  - [backend/api/api_endpoint_manager.py](backend/api/api_endpoint_manager.py)

- Frontend code
  - [frontend/js/main_dashboard_controller.js](frontend/js/main_dashboard_controller.js)
  - [frontend/js/frontend_api_client.js](frontend/js/frontend_api_client.js)

- Docs
  - [docs/backend_design.md](docs/backend_design.md) — appended recent changes section.
  - [docs/frontend_design.md](docs/frontend_design.md) — appended recent UI changes section.
  - This file: [docs/updates.md](docs/updates.md)

## Next Recommended Steps

- Apply the token protection helper (`_require_auth`) to any remaining sensitive endpoints (settings write, license create/update/delete) before broad deployment.
- Add License Renew/Suspend controls in the license list/detail UI and wire confirmation modals to the new endpoints.
- Decide how to populate address options for the Add Contract combo (settings-managed list, sync from existing companies, or free-form with save).

If you want, I can now:

- apply auth enforcement across all sensitive endpoints,
- implement the Renew/Suspend UI and glue it to the backend, or
- run the app and perform an end-to-end smoke test.

-- Generated May 2, 2026
