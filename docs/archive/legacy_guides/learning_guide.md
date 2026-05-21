# Learning Guide: Understanding the System

## 1. Introduction
Welcome to the Hazardous Material Transport License Management System. This guide is designed to help new developers or system architects quickly understand the codebase and the design decisions behind it.

## 2. Navigating the Codebase
The project is structured logically to separate different concerns:
- `/backend/api/`: The entrance to the backend. Look here for endpoint definitions and validation models.
- `/services/`: The "Brain". This is where all the business logic lives. If you want to change how a license is processed, start here.
- `/database/`: The persistence layer. Includes the schema and the main connection handler.
- `/frontend/js/main_dashboard_controller.js`: The central UI logic. Handles routing and page rendering.
- `/electron/`: Configuration for the desktop shell.

## 3. Recommended Learning Path

### Step 1: The Lifecycle of a Request
Trace a simple action, like "Restoring a License":
1. Find the button in `renderDeletedContracts` (frontend).
2. See the call to `API.restoreLicense(id)` in `frontend_api_client.js`.
3. Locate the `restore_license` endpoint in `api_endpoint_manager.py`.
4. Follow the call to `license_service.restore_license(id)`.
5. Finally, see how `db.restore_license(id)` updates the database.

### Step 2: Understanding the Service Layer
Read `services/license_service.py`. Notice how it orchestrates multiple database calls into a single logical "operation". This is a key architectural pattern used throughout the system.

### Step 3: Exploring the Database
Examine `database/schema_definitions.sql`. Pay attention to the audit logs and soft-delete columns. Understand how these are used to provide enterprise-grade reliability.

## 4. Key Design Patterns
- **Service Layer**: Decouples business logic from the communication protocol (REST).
- **Observer/Interceptor**: Used in the database handler to automatically generate audit logs.
- **Debounce**: Used in the frontend to optimize search performance.
- **Stepper**: A UX pattern to simplify complex data entry.

## 5. Expanding the System
If you want to add a new feature, follow this checklist:
1. **Database**: Add the necessary table or columns to `schema_definitions.sql`.
2. **Service**: Create a new service or add methods to an existing one.
3. **API**: Expose the functionality via a new endpoint in `api_endpoint_manager.py`.
4. **Frontend**: Add a new view or update an existing one in the UI controller.
5. **Documentation**: Update the relevant docs in `/docs/`.
