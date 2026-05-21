# Project Full Structure Inventory

This file is a human-readable inventory of the current repository snapshot. It explains each folder and each tracked file, plus the role of generated or legacy artifacts that are present in the workspace.

## Repository Shape

The application is a local desktop system built from these layers:

- Electron: desktop shell and process supervision.
- Python: FastAPI backend and business logic.
- SQLite: local persistence and reporting.
- HTML/CSS/JavaScript: frontend UI.
- Docs and legacy material: architecture notes, design references, and archived training content.

## Top-Level Files

- [.gitignore](../.gitignore): ignore rules for Python caches, SQLite databases, backups, Node build output, logs, and OS metadata.
- [application_entry_point.py](../application_entry_point.py): Python launcher that prints a startup message and runs `npm start` from the project root.
- [package.json](../package.json): root Node/Electron manifest with the desktop app name, description, and `start` / `dev` scripts.
- [package-lock.json](../package-lock.json): lockfile that pins the root Node dependency graph.
- [requirements.txt](../requirements.txt): Python dependency list for FastAPI, Uvicorn, Pydantic, APScheduler, dotenv support, and requests.

## Root Metadata

- [.git/](../.git/): Git repository metadata. This is not application code.

## backend/

This folder contains the Python API and backend-side support for background tasks and notifications.

### backend/api/

- [backend/api/api_endpoint_manager.py](../backend/api/api_endpoint_manager.py): the main FastAPI application. It defines request/response helpers, error handlers, health checks, statistics routes, license CRUD routes, restore and soft-delete flows, company and vehicle listing routes, settings storage, and the `run_server()` entry point.
- [backend/api/**pycache**/](../backend/api/__pycache__/): Python bytecode cache generated at runtime.

### backend/notifications/

- [backend/notifications/license_expiry_scheduler.py](../backend/notifications/license_expiry_scheduler.py): threaded scheduler that periodically checks for expiring licenses and triggers batch notifications.
- [backend/notifications/smtp_email_notifier.py](../backend/notifications/smtp_email_notifier.py): SMTP email sender that composes expiration alerts and logs notification deliveries.

## database/

This folder contains the SQLite schema, the database access wrapper, and generated local database artifacts.

- [database/connection_handler.py](../database/connection_handler.py): the `Database` class. It opens SQLite connections with WAL mode and busy timeout, bootstraps the schema, applies compatibility migrations, manages companies, vehicles, routes, licenses, hazmat records, settings, statistics, notifications, soft delete, restore, and audit logs.
- [database/schema_definitions.sql](../database/schema_definitions.sql): canonical SQLite schema. It defines the tables for companies, vehicles, routes, licenses, hazardous materials, audit logs, settings, and notification logs, plus supporting indexes.
- [database/licenses.db](../database/licenses.db): the local SQLite database file used by the running application. This is generated runtime data, not source code.
- [database/backups/](../database/backups/): backup output directory for copied database snapshots.
- [database/**pycache**/](../database/__pycache__/): Python bytecode cache generated at runtime.

### database schema objects

- `companies`: carrier/company registry with soft-delete fields and timestamps.
- `vehicles`: vehicles linked to companies.
- `routes`: origin, destination, and optional checkpoint records.
- `licenses`: the main contract/license table linking vehicles and routes, with record numbers, license numbers, dates, status, activity location, contract type, and deletion policy fields.
- `hazardous_materials`: hazardous cargo entries tied to vehicles.
- `audit_logs`: write history for traceability.
- `settings`: key/value configuration storage.
- `notifications_log`: records of sent email notifications.

## docs/

This folder contains the project documentation, architecture guidance, diagrams, and archived learning material.

- [docs/README.md](README.md): documentation index for the canonical docs set.
- [docs/system_overview.md](system_overview.md): business-level overview of what the system does and why it exists.
- [docs/system_architecture.md](system_architecture.md): architecture summary for the Electron, FastAPI, SQLite, and frontend layers.
- [docs/database_design.md](database_design.md): database model, tables, relationships, and storage design.
- [docs/backend_design.md](backend_design.md): backend service and API design.
- [docs/frontend_design.md](frontend_design.md): frontend UI design, navigation, and visual structure.
- [docs/performance_optimization.md](performance_optimization.md): performance notes and optimization guidance.
- [docs/error_handling_and_validation.md](error_handling_and_validation.md): validation and error handling strategy.
- [docs/deployment_and_runtime.md](deployment_and_runtime.md): runtime, startup, and deployment notes.
- [docs/technology_decisions.md](technology_decisions.md): technology selection rationale.
- [docs/project_cleanup_and_refactor_log.md](project_cleanup_and_refactor_log.md): cleanup and refactor history.
- [docs/project_structure_guide.md](project_structure_guide.md): reading guide and folder map for developers.
- [docs/full_project_explanation.md](full_project_explanation.md): long-form explanation of the whole system.
- [docs/how_to_build_systems_like_this.md](how_to_build_systems_like_this.md): instructional guide about building similar systems.
- [docs/system_flows.md](system_flows.md): request and workflow flow descriptions.
- [docs/cahier des charges.pdf](cahier des charges.pdf): original project specification document.

### docs/diagrams/

These files are the architectural and flow diagrams for the project.

- [docs/diagrams/class_diagram.mmd](diagrams/class_diagram.mmd): Mermaid class diagram for key backend and domain classes.
- [docs/diagrams/class_diagram.svg](diagrams/class_diagram.svg): rendered SVG version of the class diagram.
- [docs/diagrams/component_diagram.mmd](diagrams/component_diagram.mmd): Mermaid component diagram for the application layers.
- [docs/diagrams/component_diagram.svg](diagrams/component_diagram.svg): rendered SVG version of the component diagram.
- [docs/diagrams/er_diagram.mmd](diagrams/er_diagram.mmd): Mermaid entity-relationship diagram for the SQLite schema.
- [docs/diagrams/er_diagram.svg](diagrams/er_diagram.svg): rendered SVG version of the ER diagram.
- [docs/diagrams/sequence_contract_creation.mmd](diagrams/sequence_contract_creation.mmd): sequence diagram for the contract creation workflow.
- [docs/diagrams/sequence_contract_creation.svg](diagrams/sequence_contract_creation.svg): rendered SVG version of the contract creation sequence.
- [docs/diagrams/sequence_search.mmd](diagrams/sequence_search.mmd): sequence diagram for the search workflow.
- [docs/diagrams/sequence_search.svg](diagrams/sequence_search.svg): rendered SVG version of the search sequence.
- [docs/diagrams/sequence_statistics.mmd](diagrams/sequence_statistics.mmd): sequence diagram for dashboard and statistics retrieval.
- [docs/diagrams/sequence_statistics.svg](diagrams/sequence_statistics.svg): rendered SVG version of the statistics sequence.
- [docs/diagrams/system_architecture.mmd](diagrams/system_architecture.mmd): high-level system architecture diagram.
- [docs/diagrams/system_architecture.svg](diagrams/system_architecture.svg): rendered SVG version of the architecture diagram.
- [docs/diagrams/use_case_diagram.mmd](diagrams/use_case_diagram.mmd): use-case diagram for major user actions.
- [docs/diagrams/use_case_diagram.svg](diagrams/use_case_diagram.svg): rendered SVG version of the use-case diagram.

### docs/archive/

This folder preserves old reference and training material that is no longer part of the canonical documentation set.

- [docs/archive/README.md](archive/README.md): explanation of why the archive exists and what it contains.

#### docs/archive/legacy_guides/

Legacy training and learning material.

- [docs/archive/legacy_guides/analytics.md](archive/legacy_guides/analytics.md): archived analytics-oriented guide.
- [docs/archive/legacy_guides/how_to_build_systems_like_this.md](archive/legacy_guides/how_to_build_systems_like_this.md): archived instructional material.
- [docs/archive/legacy_guides/learning_guide.md](archive/legacy_guides/learning_guide.md): archived learning guide.
- [docs/archive/legacy_guides/MASTER_SYSTEM_DESIGN_COURSE.md](archive/legacy_guides/MASTER_SYSTEM_DESIGN_COURSE.md): archived course content.
- [docs/archive/legacy_guides/TRAINING_GUIDE.md](archive/legacy_guides/TRAINING_GUIDE.md): archived training reference.
- [docs/archive/legacy_guides/USER_MANUAL.md](archive/legacy_guides/USER_MANUAL.md): archived end-user manual.
- [docs/archive/legacy_guides/technology_decisions.md](archive/legacy_guides/technology_decisions.md): older technology decision write-up.

#### docs/archive/legacy_reference/

Older reference documentation for structure, architecture, and setup.

- [docs/archive/legacy_reference/ARCHITECTURE.md](archive/legacy_reference/ARCHITECTURE.md): older architecture guide.
- [docs/archive/legacy_reference/FILE_STRUCTURE.md](archive/legacy_reference/FILE_STRUCTURE.md): older file structure reference.
- [docs/archive/legacy_reference/FUNCTIONS_REFERENCE.md](archive/legacy_reference/FUNCTIONS_REFERENCE.md): older function reference.
- [docs/archive/legacy_reference/PROJECT_OVERVIEW.md](archive/legacy_reference/PROJECT_OVERVIEW.md): archived project overview.
- [docs/archive/legacy_reference/PROJECT_STRUCTURE_ARCHITECTURE_GUIDE.md](archive/legacy_reference/PROJECT_STRUCTURE_ARCHITECTURE_GUIDE.md): archived structure and architecture guide.
- [docs/archive/legacy_reference/README.md](archive/legacy_reference/README.md): archive reference overview.
- [docs/archive/legacy_reference/SETUP_INSTRUCTIONS.md](archive/legacy_reference/SETUP_INSTRUCTIONS.md): archived setup instructions.
- [docs/archive/legacy_reference/TECHNICAL_DOCUMENTATION.md](archive/legacy_reference/TECHNICAL_DOCUMENTATION.md): archived technical documentation.
- [docs/archive/legacy_reference/renaming_table.md](archive/legacy_reference/renaming_table.md): archived renaming mapping table.

## electron/

This folder contains the desktop shell and preload bridge.

- [electron/main.js](../electron/main.js): Electron main process. It disables GPU acceleration, resolves a Python interpreter, starts the FastAPI backend, waits for `/api/ping`, opens the main browser window, and wires keyboard shortcuts.
- [electron/preload.js](../electron/preload.js): safe preload bridge that exposes `getApiBase`, shortcut events, and listener cleanup to the renderer.
- [electron/package.json](../electron/package.json): Electron-local package manifest that declares the Electron dependency and local start scripts.
- [electron/renderer/](../electron/renderer/): empty placeholder directory in the current checkout.

## frontend/

This folder contains the browser-style UI shown inside Electron.

### frontend root

- [frontend/index.html](../frontend/index.html): main HTML shell for the application. It defines the sidebar, top bar, content area, toast container, confirm modal, edit modal, and script/style includes.
- [frontend/pages/welcome.html](../frontend/pages/welcome.html): lightweight welcome screen content with quick action cards and a system status section.

### frontend/css/

- [frontend/css/style.css](../frontend/css/style.css): complete design system and layout stylesheet. It defines light and dark theme variables, sidebar and header styling, buttons, dropdowns, cards, modals, toasts, and the overall responsive shell.

### frontend/js/

- [frontend/js/frontend_api_client.js](../frontend/js/frontend_api_client.js): single API wrapper used by the UI. It resolves the backend base URL from Electron, centralizes fetch and JSON error handling, and exposes methods for stats, licenses, companies, vehicles, and settings.
- [frontend/js/i18n.js](../frontend/js/i18n.js): translations for English, French, and Arabic, including navigation labels, dashboard labels, form labels, validation strings, and toast text.
- [frontend/js/main_dashboard_controller.js](../frontend/js/main_dashboard_controller.js): main client controller. It manages state, navigation, theme switching, language switching, toasts, confirmation dialogs, dashboard loading, settings, search, deleted contracts, statistics charts, add-contract forms, validation, and edit modals.

## modules/

This folder preserves older UI modules from the PyQt-era implementation.

### modules/legacy_pyqt_ui/

- [modules/legacy_pyqt_ui/advanced_search_interface.py](../modules/legacy_pyqt_ui/advanced_search_interface.py): legacy PyQt search interface.
- [modules/legacy_pyqt_ui/application_settings_panel.py](../modules/legacy_pyqt_ui/application_settings_panel.py): legacy settings panel.
- [modules/legacy_pyqt_ui/contract_data_entry_form.py](../modules/legacy_pyqt_ui/contract_data_entry_form.py): legacy contract entry form.
- [modules/legacy_pyqt_ui/contract_management_table.py](../modules/legacy_pyqt_ui/contract_management_table.py): legacy contract table view.
- [modules/legacy_pyqt_ui/dashboard_overview_page.py](../modules/legacy_pyqt_ui/dashboard_overview_page.py): legacy dashboard page.
- [modules/legacy_pyqt_ui/statistics_page.py](../modules/legacy_pyqt_ui/statistics_page.py): legacy statistics page logic.
- [modules/legacy_pyqt_ui/statistics.html](../modules/legacy_pyqt_ui/statistics.html): legacy HTML view for the statistics page.
- [modules/legacy_pyqt_ui/statistics.js](../modules/legacy_pyqt_ui/statistics.js): legacy JavaScript for the statistics page.

## scripts/

This folder contains developer and packaging utilities.

- [scripts/add_test_data.py](../scripts/add_test_data.py): populates the database with synthetic companies, vehicles, routes, licenses, and hazmat records for testing.
- [scripts/build_exe.spec](../scripts/build_exe.spec): PyInstaller spec file for an older PyQt packaging flow. It references `main.py`, `ui`, and `notifications` assets and is legacy relative to the current Electron/Python stack.
- [scripts/build.bat](../scripts/build.bat): Windows build helper that installs PyInstaller and PyQt5, cleans old build output, and builds a desktop executable.

## services/

This folder contains domain logic and orchestration.

- [services/background_job_manager.py](../services/background_job_manager.py): async background manager for database backups and a simulated expiry notification task.
- [services/business_rules_engine.py](../services/business_rules_engine.py): business validation rules for license creation and restore checks.
- [services/license_service.py](../services/license_service.py): orchestration layer that creates full license records by coordinating company, vehicle, route, hazmat, and audit operations.
- [services/statistics_service.py](../services/statistics_service.py): dashboard statistics service with an in-memory cache and aggregate queries.

## What the Main Files Contain

### Startup path

- `application_entry_point.py` starts the desktop app by calling Electron through npm.
- `electron/main.js` starts the backend and opens the UI only after the API is ready.
- `backend/api/api_endpoint_manager.py` exposes the HTTP interface used by the renderer.

### Data path

- `database/schema_definitions.sql` defines the tables.
- `database/connection_handler.py` performs the actual reads, writes, migrations, search queries, and soft deletes.
- `services/license_service.py` coordinates full record creation.
- `services/business_rules_engine.py` enforces policy.

### UI path

- `frontend/index.html` provides the shell.
- `frontend/css/style.css` styles the app.
- `frontend/js/main_dashboard_controller.js` drives the interface.
- `frontend/js/frontend_api_client.js` sends all API requests.
- `frontend/js/i18n.js` localizes labels and messages.

## Notes on Generated or Legacy Content

- `database/licenses.db`, `database/backups/`, and `__pycache__/` folders are generated at runtime.
- `docs/diagrams/*.svg` are rendered outputs of the Mermaid `.mmd` files.
- `docs/archive/` and `modules/legacy_pyqt_ui/` preserve older material for reference, not the active runtime path.
- `scripts/build_exe.spec` and `scripts/build.bat` belong to an older packaging path and should be treated as legacy unless the project returns to that flow.
