# System Architecture

This repository implements a local desktop administration system, not a web SaaS product. The actual runtime is a small Electron shell that launches a Python FastAPI process, which in turn talks to a single SQLite database file through a thin data-access wrapper. The source code also contains a legacy PyQt UI under `modules/legacy_pyqt_ui`, but that code is retained as reference material rather than part of the active runtime path.

## System Refinements

- `backend/api/auth_router.py` and `services/auth_service.py` provide the login/session flow that is active in the desktop shell.
- `frontend/pages/welcome.html` is a landing screen that sits between login and the main dashboard.
- The Settings page supports account profile security controls (password modification), theme selection, language selectors, and logout. All email and backup controls have been removed.
- `renderDeletedContracts()` and the restore flow are fully integrated, ensuring compliance safety via soft-deletes.
- `main.py` is a thin wrapper that launches `npm start`; it is the user-facing bootstrap entry point.
- **Separated Driver & Vehicle Entities**: Drivers and vehicles are now independent entities with dedicated views. The `drivers` table uses an auto-incrementing system-generated ID with an optional phone field.
- **Segmented Expirations**: Dashboard expiry queries are segmented into 30/60/90 day ranges. Previews are limited to 5 records and filtered entirely on the backend for performance.
- **Settings & Background Jobs Cleanup**: Completely removed SMTP, email notifications, backup systems, database tables (`notifications_log`), and background job managers/threads.

## 1. System Architecture Diagram

### Diagram

```mermaid
flowchart LR
	User[Operator]

	subgraph Launcher[Startup and desktop shell]
		MainPy[main.py]
		PackageJson[package.json / npm start]
		ElectronMain[electron/main.js]
		Preload[electron/preload.js]
		Login[frontend/pages/login.html]
		Shell[frontend/index.html]
		Controller[frontend/js/main_dashboard_controller.js]
		Client[frontend/js/frontend_api_client.js]
		I18N[frontend/js/i18n.js]
	end

	subgraph Backend[Python backend]
		API[backend/api/api_endpoint_manager.py]
		AuthRouter[backend/api/auth_router.py]
		AuthSvc[services/auth_service.py]
		LicenseSvc[services/license_service.py]
		Rules[services/business_rules_engine.py]
		StatsSvc[services/statistics_service.py]
		DB[database/connection_handler.py]
	end

	subgraph Storage[Persistence]
		Schema[database/schema_definitions.sql]
		SQLite[(database/licenses.db)]
		Audit[(audit_logs)]
		Settings[(settings)]
	end

	subgraph Legacy[Reference only]
		LegacyUI[modules/legacy_pyqt_ui/*]
	end

	User --> MainPy --> PackageJson --> ElectronMain
	ElectronMain --> Preload --> Login
	ElectronMain --> Shell
	Shell --> Controller --> Client
	Client --> API
	Client --> AuthRouter

	API --> AuthRouter
	API --> AuthSvc
	API --> LicenseSvc
	API --> StatsSvc

	AuthRouter --> AuthSvc
	AuthSvc --> DB
	LicenseSvc --> Rules
	LicenseSvc --> DB
	Rules --> DB
	StatsSvc --> DB

	DB --> Schema
	DB --> SQLite
	DB --> Audit
	DB --> Settings

	LegacyUI -. historical reference .-> DB
	I18N -. labels only .-> Controller
```

### Explanation

- `main.py` exists as the top-level launcher, and `package.json` routes that launch into Electron. If this wrapper were absent, the project would no longer present as a single desktop application entry point.
- `electron/main.js` owns process supervision: it starts Python, polls `/api/ping`, and only then opens the browser window. That startup gate matters because the renderer expects a live API immediately. Without it, the UI would race the backend and fail on first load.
- The renderer side is split into `login.html`, `index.html`, `main_dashboard_controller.js`, `frontend_api_client.js`, and `i18n.js`. Those pieces exist so the UI can be display-only, localized, and decoupled from backend transport details.
- `backend/api/api_endpoint_manager.py` is the HTTP boundary. It receives requests, validates payloads, and delegates work to services instead of mutating the database directly. `auth_router.py` is separate so authentication can be isolated from the rest of the REST surface without circular imports.
- `services/license_service.py` exists because contract creation touches several tables in one unit of work. `services/business_rules_engine.py` exists so those rules can be changed without rewriting endpoints.
- `services/statistics_service.py` exists because dashboard aggregation is read-heavy and benefits from caching. Predefined Sétif commune boundaries are loaded and statistics are aggregated using `licenses.activity_location` strictly aligned against `frontend/data/setif_communes.json`.
- `database/connection_handler.py` exists as the single SQLite access boundary. It owns WAL mode, busy-timeout retries, schema bootstrap, migrations, cache invalidation, and audit logging.
- `database/schema_definitions.sql` exists as the canonical schema source. `database/licenses.db` is the actual local data store.

---

## 2. Component Diagram

### Diagram

```mermaid
flowchart TB
	subgraph Desktop[Desktop presentation]
		LoginUI[login.html]
		MainUI[index.html]
		Welcome[pages/welcome.html]
		Controller[main_dashboard_controller.js]
		APIClient[frontend_api_client.js]
		Locale[i18n.js]
	end

	subgraph Host[Electron host]
		ElectronMain[electron/main.js]
		Preload[electron/preload.js]
		IPC[ipcMain + contextBridge]
	end

	subgraph HTTP[FastAPI boundary]
		API[api_endpoint_manager.py]
		AuthRouter[auth_router.py]
	end

	subgraph Domain[Services]
		AuthSvc[AuthService]
		LicenseSvc[LicenseService]
		Rules[BusinessRules]
		StatsSvc[StatisticsService]
	end

	subgraph Data[Persistence]
		DB[Database]
		Schema[schema_definitions.sql]
		SQLite[(licenses.db)]
	end

	LoginUI --> APIClient
	MainUI --> Controller --> APIClient
	Welcome --> Controller
	Controller --> Locale

	ElectronMain --> IPC --> Preload --> APIClient
	ElectronMain --> API

	APIClient --> API
	API --> AuthRouter
	API --> AuthSvc
	API --> LicenseSvc
	API --> StatsSvc

	AuthRouter --> AuthSvc
	LicenseSvc --> Rules
	AuthSvc --> DB
	LicenseSvc --> DB
	Rules --> DB
	StatsSvc --> DB

	DB --> Schema
	DB --> SQLite
```

### Explanation

- The presentation components keep the desktop shell understandable: `login.html` handles sign-in, `index.html` hosts the authenticated shell, `welcome.html` provides a landing page, `main_dashboard_controller.js` controls navigation and page rendering, `frontend_api_client.js` centralizes HTTP calls, and `i18n.js` manages translated strings.
- `electron/main.js` and `electron/preload.js` form the host boundary. `main.js` starts the backend and supervises readiness; `preload.js` exposes only the minimum bridge needed by the renderer.
- `api_endpoint_manager.py` and `auth_router.py` are the HTTP façade. They exist so the renderer never talks to SQLite directly.
- `AuthService`, `LicenseService`, `BusinessRules`, and `StatisticsService` are separated by responsibility.

---

## 3. Use Case Diagram

### Diagram

```mermaid
flowchart LR
	Operator([Operator])
	Admin([Administrator])
	Bootstrap([First-run bootstrap])

	Login((Log in))
	Dashboard((View dashboard))
	Create((Create contract))
	Search((Search contracts))
	Edit((Edit contract))
	Delete((Soft-delete contract))
	Restore((Restore contract))
	Stats((View statistics))
	Settings((Manage settings))
	DefaultAdmin((Create default admin))

	Operator --> Login
	Operator --> Dashboard
	Operator --> Create
	Operator --> Search
	Operator --> Edit
	Operator --> Delete
	Operator --> Restore
	Operator --> Stats
	Operator --> Settings

	Admin --> Settings
	Admin --> Restore

	Bootstrap --> DefaultAdmin

	Dashboard -. depends on .-> Login
	Create -. depends on .-> Login
	Search -. depends on .-> Login
	Stats -. depends on .-> Login
```

### Explanation

- `Operator` is the main human user of the system. The active UI lets that user log in, view the dashboard, create contracts, search records, edit contracts, soft-delete contracts, restore deleted records, and view statistics.
- `Administrator` is a narrower operational role. The settings management and restore operations are restricted or managed by this user.
- `First-run bootstrap` creates a default admin account on first run if no users exist.

---

## 4. Class Diagram

### Diagram

```mermaid
classDiagram
	class Database {
		+db_file
		+_stats_cache
		+_advanced_stats_cache
		+_advanced_stats_cached_at
		+init_database()
		+_run_migrations()
		+_get_connection()
		+_execute_write()
		+add_audit_log()
		+create_user()
		+get_user_by_username()
		+update_user_password()
		+update_username(current_username, new_username)
		+add_company()
		+get_companies()
		+get_company_by_id()
		+get_company_by_registration()
		+add_vehicle()
		+get_vehicles()
		+get_vehicles_by_company()
		+get_vehicle_by_id()
		+get_vehicle_by_registration()
		+add_route()
		+get_routes()
		+add_driver()
		+get_drivers()
		+add_license()
		+get_all_licenses()
		+search_licenses()
		+search_deleted_licenses()
		+get_license_by_id()
		+update_license()
		+soft_delete_license()
		+restore_license()
		+get_expiring_licenses()
		+add_hazmat()
		+get_hazmats_by_vehicle()
		+get_setting()
		+set_setting()
		+get_all_settings()
		+get_statistics()
		+get_advanced_statistics()
		+get_monthly_transports()
		+delete_company()
		+delete_vehicle()
		+delete_license()
	}

	class AuthService {
		+db
		+_active_tokens
		+ensure_default_admin()
		+login(username, password)
		+logout(token)
		+validate_token(token)
		+change_password(username, new_password)
		+change_username(current_username, new_username)
		+user_exists(username)
	}

	class AuthRouter {
		+create_auth_router(auth_service)
	}

	class LicenseService {
		+db
		+rules
		+create_complete_license(data)
		+soft_delete_license(license_id)
		+restore_license(license_id)
	}

	class BusinessRules {
		+db
		+validate_license_creation(data)
		+can_restore_license(license_id)
	}

	class StatisticsService {
		+db
		+get_dashboard_statistics()
		+_get_activity_series(cursor, group_expression, label_key, window_days)
		+_get_expiry_forecast(cursor)
	}

	class Company {
		+id
		+name
		+registration_number
		+address
		+carrier_type
		+account_type
		+is_deleted
		+deleted_at
		+created_at
	}

	class Vehicle {
		+id
		+company_id
		+registration_number
		+type
		+category
		+is_deleted
		+deleted_at
		+created_at
	}

	class Driver {
		+id
		+company_id
		+name
		+phone
		+is_deleted
		+created_at
	}

	class Route {
		+id
		+origin
		+destination
		+checkpoints
		+is_deleted
		+deleted_at
		+created_at
	}

	class License {
		+id
		+vehicle_id
		+route_id
		+record_number
		+driver_name
		+driver_phone
		+license_number
		+signature_date
		+expiration_date
		+status
		+activity_location
		+contract_type
		+deletion_days
		+is_deleted
		+deleted_at
		+created_at
	}

	class HazardousMaterial {
		+id
		+vehicle_id
		+material_type
		+is_deleted
		+deleted_at
		+created_at
	}

	class AuditLog {
		+id
		+action
		+table_name
		+record_id
		+old_values
		+new_values
		+user_id
		+timestamp
	}

	class Setting {
		+id
		+key
		+value
		+updated_at
	}

	class User {
		+id
		+username
		+password_hash
		+role
		+created_at
		+updated_at
	}

	AuthRouter --> AuthService
	LicenseService --> BusinessRules
	LicenseService --> Database
	BusinessRules --> Database
	StatisticsService --> Database
	AuthService --> Database

	Company "1" --> "0..*" Vehicle : owns
	Company "1" --> "0..*" Driver : employs
	Vehicle "1" --> "0..*" License : carries
	Vehicle "1" --> "0..*" HazardousMaterial : logs
	Route "1" --> "0..*" License : referenced by
	User "1" --> "0..*" AuditLog : authored by
```

---

## 5. Engineering Analysis & Refactoring Decisions

### Entity Separation (Vehicles, Drivers, and Contracts)
Vehicles, Drivers, and Contracts are now strictly decoupled into distinct views and schemas:
- **Vehicles View**: Displays registration number, type, category, and associated company. No contracts or drivers context is leaked here.
- **Drivers View**: Displays system-generated ID, driver name, optional phone number, and associated company. Drivers are fully independent entities linked to contracts.
- **Contracts View**: Displays license, route, driver name, and vehicle registration.

### Auto-Increment Driver ID Logic
The `drivers` table features a system-generated, auto-incrementing `id` as the primary key. Driver records are synchronized during contract creation or update operations. This auto-incremented primary key ensures drivers remain unique, independent entities, and prevents manual alterations of driver identifiers.

### Optional Phone Field Design Decision
In compliance with data collection guidelines and system flexibility, the driver's phone number is optional (`NULL` allowed). Operators can register drivers with a name and company link without having to supply a contact number.

### Expiration Segmentation Design
To ensure optimal performance and scalability, the "Expiring Contracts" section on the dashboard uses a tabbed switcher for 30, 60, and 90 days:
- Previews are fetched with a backend limit of 5.
- Users can click "View Full List" to load the complete dataset for that range.
- All filtering is executed on the database/backend level via SQL queries, preventing full-dataset load overhead on the client side.

### Removal of Background Services Rationale
All SMTP configurations, test email routines, database backup handlers, and background scheduler threads/job managers have been completely removed. In a local desktop app context:
- External mail/scheduler threads introduce unnecessary complexity, background thread leaks, and socket security risks.
- Removing them reduces resource footprint, improves starting and stopping sequence safety, and avoids security risks associated with storing SMTP credentials locally.

### Indexing Strategy
B-Tree indexes are preserved on critical fields like vehicle registration numbers to guarantee fast, sub-millisecond lookups during search queries and validation checks.

### Username Change & Contact Us Centralization
- **Username Change Flow**: Requires backend verification using the user's current password. Session state (token) is programmatically synchronized to prevent the operator from being signed out during renames. Password confirmation is mandatory to ensure credential owner authorization.
- **Centralized Contact Us Section**: Integrated into the Settings panel as an elegant, interactive card containing mailto links. Placing it here provides the operator with immediate support access and centralizes developer credentials cleanly.
- **Vehicle ID Auto-Increment**: The vehicle `id` field uses a unique system-generated AUTOINCREMENT schema to prevent duplicates, remain stable after deletions, and guarantee long-term integrity of foreign key relations.

---

## 6. References

- [Database Design](database_design.md)
- [System Flows](system_flows.md)
- [Project Structure Guide](project_structure_guide.md)
