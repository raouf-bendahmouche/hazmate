# System Overview

## 1. Business Purpose

The Hazardous Material Transport License Management System is a local desktop platform for managing hazardous transport license contracts with traceability, operational visibility, and compliance-oriented data retention.

Its role is to replace fragmented manual tracking with a structured system that can answer high-value operational questions quickly:
- Which licenses are active, inactive, or near expiry?
- Which company and vehicle are attached to each contract?
- What changed, when, and why?
- Which notifications were sent and when?

## 2. Scope

This is a desktop-first local application.

Included in scope:
- Electron-based user interface.
- Python FastAPI backend for logic and orchestration.
- SQLite local persistence.
- Local background scheduler for expiration checks.
- Local backup generation.

Explicitly out of scope:
- Cloud-hosted multi-tenant architecture.
- Shared remote relational database.
- Browser-only deployment mode.

## 3. Primary Users

- Operations staff entering and updating transport contracts.
- Compliance staff monitoring expirations and historical changes.
- Local administrators handling runtime settings and recovery operations.

## 4. Core Capabilities

### 4.1 Contract Lifecycle

- Create complete license contracts across company, vehicle, route, and hazardous material entities.
- Update contract fields with validation guardrails.
- Soft-delete records without irreversible loss.
- Restore soft-deleted contracts when dependencies are valid.

### 4.2 Search and Retrieval

- Multi-field search with pagination and sorting.
- Filter by status, carrier type, activity location, and contract type.
- Separate active and deleted-contract views.

### 4.3 Analytics and Monitoring

- Dashboard KPIs for carrier activity and distribution.
- Municipality-level analysis.
- Time-windowed activity trends.
- Expiration forecast and expiring-license monitoring.

### 4.4 Settings and Notifications

- Runtime key-value settings store.
- SMTP configuration for expiration alerts.
- Notification log persistence for traceability.

### 4.5 Operational Reliability

- Daily backup loop.
- Database migrations on startup.
- Soft-delete and audit log support for compliance continuity.

## 5. System Value Proposition

The system creates value in three layers:
- **Operational control**: staff can quickly find, update, and validate records.
- **Compliance readiness**: audit and soft-delete behavior preserve change history.
- **Maintainability**: architecture separates UI, API, services, and persistence boundaries.

## 6. Data Responsibility Model

The central business object is the license contract. Supporting objects exist to avoid duplication and preserve normalized relationships:
- Company data is managed independently from license rows.
- Vehicles are linked to companies and licenses.
- Routes are independent records linked to licenses.
- Hazardous material records are tied to vehicles.
- Audit logs capture every mutation of critical records.

## 7. Runtime Boundaries

Entry points:
- Desktop launcher: `npm start` from the workspace root.
- Optional Python bootstrap helper: `application_entry_point.py`.
- Backend API process: `backend/api/api_endpoint_manager.py`.

Runtime interfaces:
- Electron renderer calls backend via HTTP.
- Electron main process ensures backend readiness before opening UI.
- Backend operates against SQLite with constrained and indexed queries.

## 8. Quality Characteristics

- **Local reliability**: no external service required for core workflows.
- **Traceability**: every mutation can be audited.
- **Recoverability**: data can be restored from soft-delete or backups.
- **Performance**: statistics caching and paginated search protect responsiveness.
- **Extensibility**: service-oriented backend allows incremental feature growth.

## 9. References

- [System Architecture](system_architecture.md)
- [Database Design](database_design.md)
- [Backend Design](backend_design.md)
- [Frontend Design](frontend_design.md)
