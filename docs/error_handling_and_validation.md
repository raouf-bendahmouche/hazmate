# Error Handling and Validation

## 1. Purpose

This document explains how the system prevents invalid data, reports failures, and preserves auditability when something goes wrong.

## 2. Validation Layers

### 2.1 Frontend Validation

The renderer performs immediate checks to improve user experience, utilizing a stateful Touched/Dirty UX pattern to avoid preemptive error indicators.

Examples & Mechanics:
- Required fields must be filled before submission.
- Inputs are not visually decorated with invalid indicators (`.input-invalid`) or validation texts until they are marked as `.touched` (on focus blur or edit input) or the form is marked as `.submitted` (during a submit action).
- The submit button starts disabled on page load and evaluates form-wide validity upon input changes, ensuring no invalid payload is transmitted.
- Basic formatting rules (like checking for digits-only or letters-only) reduce avoidable backend validation errors.
- Dangerous actions require confirmation.

Why this layer exists:
- It provides non-intrusive instant feedback.
- It prevents early-trigger validation errors that ruin the user experience.
- It saves users from waiting for backend validation loops for obviously incorrect or incomplete entries.

### 2.2 API Validation

FastAPI and Pydantic validate payload structure and types.

Examples:
- `LicenseCreate` and `LicenseUpdate` define accepted request shapes.
- Query parameters are normalized before use.

Why this layer exists:
- It protects the service layer from malformed input.
- It keeps endpoint behavior predictable.

### 2.3 Business Validation

The business rules layer enforces domain logic that cannot be expressed as field typing alone.

Examples:
- Vehicle registration is mandatory for a contract.
- A registration number must exist before creation.
- A deleted record can only be restored if dependent entities are still available.

Why this layer exists:
- It captures policy, not just syntax.
- It keeps rule changes in one place.

### 2.4 Database Validation

SQLite constraints are the final safety net.

Examples:
- Unique registration (record) and internal license numbers.
- Foreign key relationships.
- Non-null constraints on critical columns.

Why this layer exists:
- It prevents corruption even if higher layers fail.

## 3. Error Response Strategy

The API returns normalized JSON responses.

Success:
```json
{
  "status": "success",
  "message": "ok",
  "data": {}
}
```

Error:
```json
{
  "status": "error",
  "message": "Readable explanation"
}
```

Why this matters:
- The frontend can display a consistent message regardless of endpoint.
- The user does not need to interpret raw Python tracebacks.

## 4. Exception Handling Model

- `404` handler normalizes unknown routes.
- `HTTPException` handler returns API-consistent errors.
- Generic exception handler prevents a backend crash from leaking implementation details.

Why this matters:
- The app must fail safely.
- A single unexpected exception should not take down the whole desktop session.

## 5. User-Facing Feedback

The renderer should present errors in the correct context.

- Inline validation for form issues.
- Toast notifications for API failures.
- Confirmation modals for destructive actions.

Why this matters:
- Users need to know whether they can fix the issue immediately or whether support is required.

## 6. Auditability and Recovery

- Every mutation is written to `audit_logs`.
- Notification sends are written to `notifications_log`.
- Soft delete preserves records for restore and inspection.

Why this matters:
- Compliance workflows require traceable history.
- Deleted data can be restored instead of permanently lost.

## 7. Common Failure Modes

- Missing required form input.
- Duplicate unique values.
- SQLite lock contention.
- SMTP credentials missing or invalid.
- Backend not running when the renderer starts.

Mitigation pattern:
- Validate early.
- Retry transient database writes.
- Degrade gracefully when notification configuration is absent.
- Use the backend health check before opening the main UI.

## 8. Operational Debugging

The main process logs backend stdout and stderr.

Why this matters:
- Local desktop applications need a clear diagnostic trail.
- If the Python process fails to start, the issue should be visible without attaching a debugger.

## 9. References

- [Backend Design](backend_design.md)
- [System Architecture](system_architecture.md)
- [Deployment and Runtime](deployment_and_runtime.md)