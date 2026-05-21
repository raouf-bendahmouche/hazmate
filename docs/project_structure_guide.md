## Project Structure Guide

This file explains the important folders and files and suggests a reading order to understand the project.

**Top-level (what to open first):**

- `application_entry_point.py`: bootstraps the Electron/desktop startup. Good first read to see how the app is launched.
- `backend/api/api_endpoint_manager.py`: primary HTTP API surface. Read after the entry point to learn endpoints and the overall lifecycle.
- `database/connection_handler.py`: core DB access, schema bootstrapping, caching, and helpers. Essential to understand data model and queries.

**Folders and important files:**

- `backend/`:
  - `api/api_endpoint_manager.py`: FastAPI app routes and lifecycles.
  - `notifications/license_expiry_scheduler.py`: background scheduler for notifications.
  - `notifications/smtp_email_notifier.py`: email notifier implementation.

- `database/`:
  - `connection_handler.py`: `Database` class — handles connections, schema migration, read/write helpers, statistics cache, search logic, and soft-delete semantics.
  - `schema_definitions.sql`: canonical schema used at first-run bootstrap.

- `services/`:
  - `license_service.py`: service layer orchestrating license creation, soft-delete & restore.
  - `statistics_service.py`: analytics + in-memory caching for dashboard.
  - `background_job_manager.py`: backup and async background tasks.
  - `business_rules_engine.py`: domain validation rules.

- `modules/legacy_pyqt_ui/`: contains older PyQt UI components. Useful for domain-specific GUI patterns and reference but not the Electron UI.

- `frontend/` and `electron/`:
  - `electron/main.js`, `preload.js`, `renderer/` and `frontend/js/*`: the renderer/app UI that talks to the local API.

- `services/` and `backend/` contain the business logic and are the most important for engineers wanting to modify behavior.

**Suggested reading order to learn the system:**

1. `application_entry_point.py` — see how UI and API are launched together.
2. `electron/main.js` and `frontend/index.html` — learn UX flows and where API calls originate.
3. `backend/api/api_endpoint_manager.py` — map UI actions to API routes.
4. `services/license_service.py` and `services/business_rules_engine.py` — understand orchestration and domain rules.
5. `database/connection_handler.py` and `database/schema_definitions.sql` — inspect data layout, constraints, and search/aggregation queries.
6. `services/statistics_service.py` & `services/background_job_manager.py` — learn caches and background tasks.
7. `backend/notifications/*` — how notifications are generated and logged.
8. `modules/legacy_pyqt_ui` — optional: legacy UI patterns and helper code.

This order provides a path from high-level UX to the persistent storage and background concerns, and it matches typical developer tasks (feature work, bug fixes, DB migrations).

# Project Structure Guide

This repository is organized as a local desktop application with a thin Electron shell, a Python FastAPI backend, a SQLite storage layer, and a browser-style frontend. This guide explains where each part lives, why it exists, and how to read the code in a useful order when you are new to the project.

## 1. How to Explore the Project

If you are joining the project for the first time, read it in this order:

1. Start with `docs/system_overview.md` to understand the business purpose.
2. Read `docs/system_architecture.md` and then `docs/full_project_explanation.md` to understand the runtime shape of the application.
3. Open `application_entry_point.py` and `package.json` to see how the desktop app starts.
4. Read `database/schema_definitions.sql` and `database/connection_handler.py` to understand the persistent data model and how SQLite is used.
5. Read `services/license_service.py` and `services/business_rules_engine.py` to see how contract creation and validation actually work.
6. Read `backend/api/api_endpoint_manager.py` to see how HTTP requests are exposed.
7. Read `frontend/index.html`, `frontend/js/main_dashboard_controller.js`, and `frontend/js/frontend_api_client.js` to see how the UI renders pages and talks to the backend.

This order matters because the project is easiest to understand from the outside in: purpose, architecture, entry point, data model, business rules, API boundary, then UI behavior.

## 2. Folder Map

### `/backend/`

This folder contains the FastAPI application and backend-side support code. It exists to expose the application’s business capabilities over HTTP and to manage side effects such as background jobs and notifications. Files here should usually be route handlers, API validation models, scheduler logic, notification helpers, and other code that must run on the server side rather than in the UI.

### `/database/`

This folder contains the SQLite schema, the database connection wrapper, and backup-related files. It exists to keep persistent storage concerns separate from business logic. Files here should define tables, manage connections, run migrations, and perform data access or backup operations. If you are looking for the truth of what is stored and how records are related, this is the place to start.

### `/docs/`

This folder contains the project’s learning and reference material. It exists so the system can be understood without reading every source file first. Files here should explain architecture, database design, deployment, performance, validation, cleanup history, and developer guidance. New contributors should use these documents to build context before editing code.

### `/electron/`

This folder contains the desktop wrapper that starts the backend and hosts the UI. It exists to turn the web frontend and Python backend into a single local application. Files here should manage app lifecycle, subprocess startup, process supervision, preload bridges, and any Electron packaging logic.

### `/frontend/`

This folder contains the user interface assets: HTML, CSS, and JavaScript. It exists to render the desktop experience and collect user input. Files here should include the shell markup, visual styles, localization strings, API client wrappers, and the main controller that handles routing and page rendering.

### `/modules/`

This folder contains legacy or archived functional modules. It exists so older UI or feature code can be preserved for reference without being part of the active desktop runtime. Files here are usually older PyQt-era components or isolated historical artifacts rather than current production paths.

### `/scripts/`

This folder contains helper scripts for development and packaging. It exists to automate repeatable tasks such as seeding data, building binaries, or producing distribution artifacts. Files here should be operational tools, not core application logic.

### `/services/`

This folder contains the domain and orchestration layer. It exists to keep business rules out of the API layer and to centralize workflows such as license creation, statistics computation, and background management. Files here should contain the real application logic that coordinates database operations, validations, and domain-specific policy.

## 3. Important Files and How to Read Them

### `application_entry_point.py`

This is the top-level launcher. It tells you how the project starts from the user’s perspective. Read this first if you want to understand what command actually boots the app.

### `package.json`

This is the Electron runtime manifest. It defines the Node/Electron startup scripts and dependency metadata. Read this early because it explains how the desktop shell is launched.

### `frontend/index.html`

This is the UI shell. It contains the persistent page frame, navigation regions, and containers that the JavaScript controller fills in at runtime. Read it early when learning the visual structure of the app.

### `frontend/js/main_dashboard_controller.js`

This is the main client-side controller. It contains routing, page rendering, search behavior, form submission logic, and many of the UI event handlers. Read it after you understand the page shell because it is the file that makes the interface interactive.

### `frontend/js/frontend_api_client.js`

This is the frontend API bridge. It wraps HTTP calls to the backend in one place so UI code does not need to know request details. Read it later unless you are changing API endpoints or debugging request behavior.

### `backend/api/api_endpoint_manager.py`

This is the HTTP boundary for the Python backend. It defines the FastAPI routes, request models, error handling, and lifecycle hooks. Read it when you need to trace a user action from the UI into the server.

### `services/license_service.py`

This is the most important business workflow file for contract creation and lifecycle operations. It coordinates company, vehicle, route, hazmat, and audit records. Read it when you want to understand how a single contract becomes a complete persisted record.

### `services/business_rules_engine.py`

This file contains validation and policy checks. Read it after the license service because it tells you which business constraints must hold before data can be saved or restored.

### `database/schema_definitions.sql`

This file defines the SQLite tables and relationships. Read it early because the schema explains what kinds of records exist and how they relate to each other.

### `database/connection_handler.py`

This file manages SQLite access, migrations, caching invalidation, and writes. Read it after the schema because it shows how the data model is actually stored and updated.

### `docs/system_architecture.md`

This is the best document for understanding component boundaries, startup order, and request flow. Read it when you want the structural view of the application.

### `docs/full_project_explanation.md`

This is the best document for a deep narrative explanation of the whole system. Read it after the architecture document if you want a slower, more explanatory walkthrough.

## 4. What Each Area Helps You Learn

If you want to understand architecture, start with the documentation in `docs/system_architecture.md` and `docs/full_project_explanation.md`, then confirm the implementation in `electron/main.js`, `backend/api/api_endpoint_manager.py`, and `frontend/js/main_dashboard_controller.js`.

If you want to understand business logic, start with `services/license_service.py` and `services/business_rules_engine.py`, then follow how those services are called from the API layer.

If you want to understand the database, read `database/schema_definitions.sql` first and then `database/connection_handler.py` to see how the schema is used in real queries and migrations.

If you want to understand the UI, start with `frontend/index.html`, then read `frontend/js/main_dashboard_controller.js`, and then inspect `frontend/css/style.css` for the visual behavior.

If you want to understand data flow, follow one request end-to-end: `frontend/js/main_dashboard_controller.js` calls `frontend/js/frontend_api_client.js`, which sends HTTP requests to `backend/api/api_endpoint_manager.py`, which delegates to `services/license_service.py`, which reads and writes through `database/connection_handler.py` into the SQLite database.

## 5. Practical Reading Advice

Do not start with the largest JavaScript file and try to read it top to bottom. Instead, search for the page or function you are changing, follow the call chain, and only then widen your reading.

Treat the documentation as part of the architecture, not as an afterthought. The docs explain design intent, while the source files show the actual implementation. Reading both together is the fastest way to understand this project cleanly.
