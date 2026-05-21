# Project Reorganization & Naming Convention

## 1. Directory Structure Changes
The system has been reorganized into logical modules to improve maintainability and follow industrial standards.

| Old Directory | New Directory | Reason |
| :--- | :--- | :--- |
| `/` (root) | `/backend/api/` | Decoupling core API logic from root. |
| `/` (root) | `/database/` | Centralizing persistence concerns. |
| `/` (root) | `/services/` | Implementing a dedicated business logic layer. |
| `/` (root) | `/frontend/` | Grouping all UI assets (HTML/CSS/JS). |
| `/` (root) | `/docs/` | Centralizing all technical and engineering documentation. |

## 2. File Renaming Table
To ensure self-explanatory naming, the following files have been renamed:

| Old Name | New Name | Reason |
| :--- | :--- | :--- |
| `main.py` | `application_entry_point.py` | Clearly identifies the startup script. |
| `db.py` | `database/connection_handler.py` | Specific role in managing SQLite connections. |
| `api.py` | `backend/api/api_endpoint_manager.py` | Highlights its role as an endpoint orchestrator. |
| `scheduler.py` | `backend/notifications/license_expiry_scheduler.py` | Describes the specific scheduling task. |
| `styles.css` | `frontend/css/style.css` | Standardized path for UI styling. |
| `app.js` | `frontend/js/main_dashboard_controller.js` | Clarifies its role as the central UI state manager. |

## 3. Naming Principles
- **Descriptive over Concise**: Prefer `get_license_by_registration` over `get_lic_reg`.
- **Module-based grouping**: Services live in `/services/`, models in `/models/` (if any), and UI in `/frontend/`.
- **Consistency**: All backend Python files use `snake_case`, while frontend JS files use `camelCase` (with some `snake_case` for controller names).
