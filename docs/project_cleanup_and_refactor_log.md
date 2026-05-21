# Project Cleanup and Refactor Log

## 1. Purpose

This file records the documentation rebuild, naming cleanup, and structural refactor decisions applied to the project so future maintainers can understand what changed and why.

## 2. Documentation Standardization

The workspace previously contained overlapping documentation files in mixed naming styles. The cleanup normalized the canonical documentation set in lowercase filenames and expanded each topic into a dedicated document.

### Canonical documentation files

- `system_overview.md`
- `system_architecture.md`
- `database_design.md`
- `backend_design.md`
- `frontend_design.md`
- `performance_optimization.md`
- `error_handling_and_validation.md`
- `deployment_and_runtime.md`
- `technology_decisions.md`
- `how_to_build_systems_like_this.md`

## 3. Files Added

- `docs/error_handling_and_validation.md`: Replaces the shorter legacy error handling note with a combined validation and exception strategy.
- `docs/deployment_and_runtime.md`: Replaces the shorter deployment note with a complete runtime and startup guide.
- `docs/technology_decisions.md`: Captures why each technology was selected and what alternatives were rejected.
- `docs/how_to_build_systems_like_this.md`: Educational course-style engineering guide.
- `docs/project_cleanup_and_refactor_log.md`: This file.

## 4. Files Updated

- `docs/backend_design.md`: Expanded into a detailed backend architecture and contract guide.
- `docs/frontend_design.md`: Expanded into a structured UI/UX architecture document.
- `docs/performance_optimization.md`: Expanded into a performance strategy document.

## 5. Files Removed as Redundant Duplicates

The following uppercase duplicates were removed because the lowercase canonical files are now the maintained versions:

- `docs/SYSTEM_OVERVIEW.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DATABASE_DESIGN.md`

## 6. Legacy Files Replaced by Canonical Names

- `docs/error_handling.md` was replaced by `docs/error_handling_and_validation.md`.
- `docs/deployment.md` was replaced by `docs/deployment_and_runtime.md`.
- `docs/PROJECT_CLEANUP_REORGANIZATION.md` is superseded by this log.

## 7. Why These Changes Were Made

### 7.1 Reduce redundancy

Multiple docs previously described the same concepts in different files. That made maintenance harder and increased the risk of conflicting instructions.

### 7.2 Improve discoverability

The new file names explain purpose directly, which helps new developers navigate the project quickly.

### 7.3 Preserve maintainability

Each document now has a clear scope so changes in one area do not need to be duplicated across several overlapping documents.

## 8. Runtime Codebase Notes

No core business logic was intentionally changed during the documentation pass.

Areas reviewed:

- Electron startup flow.
- FastAPI backend structure.
- SQLite schema and migrations.
- Notification and background job helpers.
- Frontend API wrapper and controller logic.

## 9. Follow-Up Work Still Worth Doing

- Add or refine comments in the most important code paths if additional maintainers need deeper in-code explanations.
- Verify whether any legacy archive documentation should remain discoverable or be further consolidated.
- Run the application end-to-end and confirm the startup flow, navigation, search, statistics, and data entry workflows.

## 10. Revert Add Contract Workflow

- **What was changed**: The split contract-entry path was removed from the UI. The contract creation flow now stays in one window again.
- **What was reverted**: The temporary multi-step / split-entry behavior that sent users to separate vehicle and driver entry screens.
- **Why it was reverted**: The previous workflow was less practical for day-to-day contract entry. The single-page form keeps all contract, company, vehicle, route, driver, and hazmat inputs together while preserving the current validation, business rules, and save behavior.
- **Files affected**:
  - `frontend/js/main_dashboard_controller.js` (Restored the main Add Contract page as the single entry surface and removed the search-result shortcuts that launched the split workflow).
  - `docs/project_cleanup_and_refactor_log.md` (This record).

## 11. Current Status of This Revert

The backend model, validation rules, persistence layer, and API contract were left unchanged. Only the UI routing and search-result actions that created the split experience were adjusted so the application returns to the previous one-window contract entry model.
