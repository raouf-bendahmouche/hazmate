# Backend Design

## 1. Purpose

This backend exists to convert user actions from the Electron UI into validated, auditable, local database operations. The design intentionally keeps the renderer thin so that business rules, persistence, and background work live in one coherent Python boundary.

## 2. Runtime Components

- `backend/api/api_endpoint_manager.py`: FastAPI application, routing, validation, lifespan hooks, and response normalization.
- `services/license_service.py`: Orchestrates multi-table contract creation and restoration rules.
- `services/statistics_service.py`: Builds dashboard-ready analytics payloads with in-memory caching.
- `services/business_rules_engine.py`: Centralizes domain checks so API handlers stay simple.
- `services/background_job_manager.py`: Handles backup loop and non-blocking background tasks.
- `backend/notifications/license_expiry_scheduler.py`: Periodic expiry checks driven by settings stored in SQLite.
- `backend/notifications/smtp_email_notifier.py`: SMTP notification integration for expiration alerts.
- `database/connection_handler.py`: SQLite connection, schema bootstrap, migrations, and query helper layer.

## 3. Layering Model

### 3.1 API Layer

The API layer exposes the external contract of the system. Its job is not to perform business logic directly, but to validate inputs, map requests to services, and return a stable JSON envelope.

Key responsibilities:

- Health checking for Electron startup readiness.
- CRUD endpoints for licenses and supporting entities.
- Settings read/write endpoints.
- Statistics endpoints for dashboard consumption.
- Consistent error translation using FastAPI exception handlers.

Why this layer matters:

- It prevents the UI from depending on raw SQL or database implementation details.
- It provides a single place to enforce payload shape and HTTP semantics.
- If removed, the frontend would need direct database access, which would destroy portability and validation discipline.

### 3.2 Service Layer

The service layer coordinates operations that touch more than one entity or rule boundary.

- `LicenseService` creates or reuses companies and vehicles, creates routes, adds hazmat records when applicable, and writes audit logs.
- `StatisticsService` performs analytics assembly and caching so the API can return dashboard data without expensive recomputation on every request.
- `BusinessRules` enforces domain constraints such as mandatory vehicle registration and restore eligibility.

Why this layer matters:

- It keeps business logic out of route handlers.
- It isolates multi-step workflows so they are easier to test and reason about.
- If removed, route handlers would become large and fragile, and changes to business rules would be harder to manage.

### 3.3 Background Layer

The background layer runs outside the request/response path and supports compliance automation.

- License expiry checks run on a scheduler thread.
- Backup creation runs asynchronously.
- SMTP notifications are only sent when configuration is available.

Why this layer matters:

- Compliance checks must continue without user interaction.
- Backup behavior must not block the UI.
- If removed, renewal monitoring and backup resilience would disappear.

### 3.4 Data Layer

The data layer owns SQLite access patterns and schema evolution.

- Creates the database file if missing.
- Applies schema definitions on startup.
- Adds missing columns for backward compatibility.
- Provides query helpers and write retry logic.
- Invalidates cached statistics after mutation.

Why this layer matters:

- It protects the rest of the backend from low-level SQLite concerns.
- It provides a consistent place to manage file-based persistence.
- If removed, every service would need to duplicate connection management and migration logic.

## 4. Request Flow

### 4.1 License Creation

1. The renderer posts a JSON payload to `POST /api/licenses`.
2. Pydantic validates field types and required values.
3. `LicenseService` validates the business rule layer.
4. The database layer creates or reuses dependent entities.
5. Audit logs record the change.
6. The API returns a normalized success envelope.

### 4.2 Search and Pagination

1. The renderer issues `GET /api/licenses` with search and filter parameters.
2. The API sanitizes pagination and sorting inputs.
3. The database layer applies indexed queries and joins.
4. The response returns items plus total count for paging controls.

### 4.3 Dashboard Statistics

1. The renderer calls `GET /api/statistics/dashboard`.
2. `StatisticsService` returns cached data when valid.
3. Otherwise it computes KPI and trend payloads from SQLite.
4. The frontend renders charts and cards from the returned structure.

## 5. API Contract Summary

- `GET /api/ping`: readiness probe.
- `GET /api/licenses`: paginated filtered listing.
- `POST /api/licenses`: create a full contract.
- `GET /api/licenses/{id}`: retrieve a single contract.
- `PUT /api/licenses/{id}`: update a contract.
- `DELETE /api/licenses/{id}`: soft-delete a contract.
- `POST /api/licenses/{id}/restore`: restore a soft-deleted contract.
- `GET /api/licenses/deleted`: inspect archived records.
- `GET /api/licenses/expiring`: preview near-expiry licenses.
- `GET /api/statistics/dashboard`: dashboard payload.
- `GET /api/stats`, `GET /api/stats/advanced`, `GET /api/stats/monthly`: compatibility endpoints.
- `GET /api/settings`, `PUT /api/settings`: runtime configuration.

## 6. Validation Strategy

Validation occurs in three places:

- UI validation prevents obviously invalid submissions.
- Pydantic rejects malformed requests.
- Domain rules reject semantically invalid workflows.

This layered approach is intentional because each layer protects against a different class of defect. If one layer is bypassed, the next layer still protects the database.

## 7. Concurrency and Lifespan

- FastAPI lifespan starts the scheduler and async background manager.
- Scheduler uses a daemon thread so it does not block shutdown.
- Backup tasks use asyncio so they do not stall API responsiveness.
- SQLite connections use retry logic for lock contention.

## 8. Design Trade-offs

- The backend favors clarity over abstraction depth because the application is local-first and the domain is relatively small.
- The system uses explicit services rather than a generic repository pattern because the orchestration steps are domain-specific and benefit from readability.
- A small number of compatibility endpoints remain so older frontend code can keep working while docs and naming are normalized.

## 9. References

- [System Overview](system_overview.md)
- [System Architecture](system_architecture.md)
- [Database Design](database_design.md)
- [Error Handling and Validation](error_handling_and_validation.md)

## Recent Changes (May 2026)

The following runtime and API changes were implemented recently and are reflected in the codebase:

- **Authentication service:** A bcrypt-backed authentication service was added to `services/auth_service.py` to support local password-based login for the desktop app. See [services/auth_service.py](services/auth_service.py).
- **Auth endpoints:** New auth endpoints were registered under `/auth` using a dedicated router: `POST /auth/login`, `POST /auth/logout`, `GET /auth/validate`, and `POST /auth/change-password`. Implementation: [backend/api/auth_router.py](backend/api/auth_router.py).
- **Endpoint protections:** A lightweight token validation helper was added and applied to write endpoints (company creation, license mutations) to require an Authorization header with a valid session token. See usage in [backend/api/api_endpoint_manager.py](backend/api/api_endpoint_manager.py).
- **Company creation duplicate checks:** `POST /api/companies` now prevents duplicate enterprises by checking registration number and name before insertion.
- **License management:** New mutation endpoints were added to support runtime business actions: `POST /api/licenses/{id}/renew` (extend license expiration) and `POST /api/licenses/{id}/suspend` (suspend/stop a contractor). These are implemented in the API manager and routed to the service layer.
- **Bootstrap admin account:** The system ensures a default admin account exists at startup (`ensure_default_admin`) to allow first-time configuration. The admin password is stored hashed in the local database.

Note: These additions are local-first and intended for desktop usage. The token store is in-memory for the app lifecycle; consider persistent session storage if deploying to shared environments.
