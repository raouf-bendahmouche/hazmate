# Project Structure Guide

This repository is organized as a local desktop application with a thin Electron shell, a Python FastAPI backend, a SQLite storage layer, and a browser-style frontend. This guide explains where each part lives, what it contains, whether it matters for day-to-day maintenance, and how to read the code in the most useful order.

## 1. Recommended Reading Order

1. Start with `docs/system_architecture.md` so you understand the actual runtime shape.
2. Read `docs/database_design.md` and `database/schema_definitions.sql` together so the schema and the diagram match in your head.
3. Open `main.py` and `package.json` to see the top-level desktop startup path.
4. Read `electron/main.js` and `electron/preload.js` to understand process supervision and the renderer bridge.
5. Read `backend/api/api_endpoint_manager.py` and `backend/api/auth_router.py` to see the HTTP surface.
6. Read `services/license_service.py` and `services/business_rules_engine.py` to understand contract creation and restore rules.
7. Read `database/connection_handler.py` to see how SQLite, migrations, caching, and backups are handled.
8. Read `frontend/index.html`, `frontend/pages/login.html`, `frontend/pages/welcome.html`, `frontend/js/frontend_api_client.js`, and `frontend/js/main_dashboard_controller.js` to see the user journey and data flow.
9. Finish with `docs/system_flows.md` if you want the end-to-end request sequences.

That order matters because the project is easiest to understand from the outside in: startup, architecture, persistence, business rules, API boundary, and then page behavior.

## 2. Folder Map

### `backend/`

This folder contains the FastAPI application and backend-side support code. It matters because it is the public HTTP boundary and the place where authentication, lifecycle hooks, and notification behavior are wired together. The active files here are `backend/api/api_endpoint_manager.py`, `backend/api/auth_router.py`, `backend/notifications/license_expiry_scheduler.py`, and `backend/notifications/smtp_email_notifier.py`.

### `database/`

This folder contains the SQLite schema, the database connection wrapper, and backup-related files. It matters the most when you are changing persistence, migration, search, restore, or statistics behavior. The key files are `database/schema_definitions.sql` and `database/connection_handler.py`, plus the live database file and backup directory.

### `docs/`

This folder contains the project’s learning and reference material. It matters because the repository now uses the docs as a first-class engineering artifact, not as optional commentary. The active documents are `system_architecture.md`, `database_design.md`, `system_flows.md`, `project_structure_guide.md`, and the supporting diagram sources under `docs/diagrams/`.

### `electron/`

This folder contains the desktop wrapper that starts the backend and hosts the UI. It matters because it is the process boundary that turns a browser frontend and Python backend into one local application. The important files are `electron/main.js` and `electron/preload.js`.

### `frontend/`

This folder contains the user interface assets: HTML, CSS, and JavaScript. It matters for every user-visible change. The important files are `frontend/index.html`, `frontend/pages/login.html`, `frontend/pages/welcome.html`, `frontend/js/frontend_api_client.js`, `frontend/js/main_dashboard_controller.js`, and `frontend/js/i18n.js`.

### `modules/legacy_pyqt_ui/`

This folder contains legacy PyQt-era components. It matters for historical reference, migration context, and feature comparison, but it is not part of the active Electron runtime. Files here include `contract_data_entry_form.py`, `contract_management_table.py`, `advanced_search_interface.py`, `application_settings_panel.py`, `dashboard_overview_page.py`, and `statistics_page.py`.

### `scripts/`

This folder contains helper scripts for development and packaging. It matters when you need to seed data, build artifacts, or produce a packaged executable. It is not part of normal runtime behavior.

### `services/`

This folder contains the domain and orchestration layer. It matters because it holds the logic that is too business-specific to belong in the API and too high-level to belong in the database wrapper. The key files are `services/license_service.py`, `services/business_rules_engine.py`, `services/statistics_service.py`, `services/background_job_manager.py`, and `services/auth_service.py`.

## 3. Key Files

### `main.py`

This is the user-facing bootstrap wrapper. It is small, but it matters because it is the command a desktop user or packaging script can run without knowing anything about Electron or Python internals.

### `package.json`

This is the Electron runtime manifest. It defines the `npm start` entry point and the Electron dependency. If this file changes incorrectly, the whole desktop shell stops launching.

### `electron/main.js`

This is the desktop orchestrator. It starts Python, waits for `/api/ping`, loads the login page, and registers keyboard shortcuts. This file matters whenever startup, process supervision, or API readiness changes.

### `electron/preload.js`

This file exposes the narrow bridge between the renderer and Electron internals. It matters because it is the security boundary that keeps the UI from gaining full Node access.

### `backend/api/api_endpoint_manager.py`

This is the main HTTP surface. It matters whenever request validation, endpoint behavior, or app lifecycle logic changes.

### `backend/api/auth_router.py`

This file defines login, logout, token validation, and password change endpoints. It matters because authentication is now a real first-class flow rather than a UI-only stub.

### `services/license_service.py`

This is the most important business workflow file for contract creation and lifecycle changes. It matters whenever the system creates, soft-deletes, or restores a contract.

### `services/business_rules_engine.py`

This file contains the validation and restore checks that protect contract integrity. It matters because those rules are the line between valid records and corrupt state.

### `services/statistics_service.py`

This file computes the dashboard payload. It matters because the dashboard is read-heavy and uses caching to stay fast.

### `services/background_job_manager.py`

This file owns the non-blocking maintenance loop and database backup behavior. It matters for reliability, not for user interaction.

### `services/auth_service.py`

This file handles password hashing, login, logout, and default admin bootstrap. It matters because the desktop app still needs session control even though it runs locally.

### `database/schema_definitions.sql`

This file defines the actual table layout. It matters whenever a field, key, or relationship changes because the schema is the source of truth.

### `database/connection_handler.py`

This file manages SQLite access, migrations, retries, cache invalidation, audit logging, and many helper queries. It matters because it is the persistence gatekeeper for almost every feature.

### `frontend/index.html`

This is the main authenticated shell. It matters because it defines the persistent layout and the navigation regions that the controller fills at runtime.

### `frontend/pages/login.html`

This is the sign-in page. It matters because it is the first user interaction with the app and the gate into the main shell.

### `frontend/pages/welcome.html`

This is the landing page shown inside the app after login. It matters less than the dashboard, but it is still part of the real navigation flow.

### `frontend/js/frontend_api_client.js`

This is the API wrapper. It matters because it centralizes request shape, token headers, and error handling.

### `frontend/js/main_dashboard_controller.js`

This is the main frontend controller. It matters most for UI work because it handles routing, dashboard rendering, search, editing, deleted-record restore, statistics charts, and settings forms.

### `frontend/js/i18n.js`

This file holds translations. It matters whenever text, language switching, or RTL/LTR behavior changes.

### `modules/legacy_pyqt_ui/*`

These files matter for learning and migration context, but not for runtime behavior. They are useful when you want to compare the current Electron implementation against the older PyQt design.

## 4. What Each Area Helps You Learn

If you want to understand architecture, start with `docs/system_architecture.md`, then confirm the implementation in `electron/main.js`, `backend/api/api_endpoint_manager.py`, and `frontend/js/main_dashboard_controller.js`.

If you want to understand business logic, start with `services/license_service.py` and `services/business_rules_engine.py`, then follow how those services are called from the API layer.

If you want to understand the database, read `database/schema_definitions.sql` first and then `database/connection_handler.py` so you can connect the schema to the real queries and migrations.

If you want to understand the UI, start with `frontend/index.html`, then read `frontend/js/main_dashboard_controller.js`, and then inspect `frontend/css/style.css` for the visual behavior.

If you want to understand authentication, read `backend/api/auth_router.py` and `services/auth_service.py` together, then see how `frontend/pages/login.html` stores the token.

If you want to understand maintenance behavior, inspect `backend/notifications/license_expiry_scheduler.py`, `backend/notifications/smtp_email_notifier.py`, and `services/background_job_manager.py`.

## 5. Discovered Additions

- `renderSettings()` exists in the main controller and is backed by `/api/settings`, even though it is easy to miss when scanning the nav flow.
- `renderDeletedContracts()` and `API.restoreLicense()` form a full archived-record recovery path.
- `backend/api/auth_router.py` adds real login/logout/password-change endpoints that are separate from the contract routes.
- `frontend/pages/welcome.html` gives the app a landing screen after sign-in.
- `modules/legacy_pyqt_ui/` includes archived search, settings, dashboard, and statistics screens that are still useful as reference material.

## 6. Practical Reading Advice

Do not start with the largest JavaScript file and try to read it top to bottom. Instead, search for the page or function you are changing, follow the call chain, and only then widen your reading.

Treat the documentation as part of the architecture, not as an afterthought. The docs explain design intent, while the source files show the actual implementation. Reading both together is the fastest way to understand this project cleanly.
