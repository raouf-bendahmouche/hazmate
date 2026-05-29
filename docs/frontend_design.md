# Frontend Design

## 1. Purpose

The frontend is the operator-facing desktop interface. It must be fast, readable, multilingual, and resilient to backend latency because users are entering compliance-sensitive data in a local desktop environment.

## 2. Frontend Structure

- `frontend/index.html`: Shell layout, navigation, content container, modal containers, and script/style loading.
- `frontend/css/style.css`: Visual system, spacing, forms, responsive layout, and component styling.
- `frontend/js/frontend_api_client.js`: All HTTP communication with the Python backend.
- `frontend/js/main_dashboard_controller.js`: View state, routing, forms, dashboard rendering, and event handling.
- `frontend/js/i18n.js`: Language switching and localized labels.
- `frontend/pages/`: Additional page fragments or legacy page assets.

## 3. User Experience Goals

The UI is designed to minimize cognitive load for high-frequency data entry tasks.

- Fast access to the dashboard and search tools.
- Prominent navigation for create/search/deleted/statistics workflows.
- Clear feedback for success, warnings, and destructive actions.
- Support for Arabic, French, and English.
- Local-first behavior so the app remains usable without external services.

## 4. Navigation Model

The interface uses a persistent sidebar and a single main content area.

Why this works:

- It keeps the application predictable.
- It reduces page-switching confusion.
- It makes the app feel like a native control panel rather than a generic website.

Navigation sections include:

- Dashboard.
- Add Contract.
- Search.
- Deleted Contracts.
- Statistics.

## 5. State Management

The main controller keeps a small state object for:

- Current page.
- Navigation history.
- Theme selection.
- Search timers and chart instances.

Why the state is intentionally small:

- Desktop UI workflows are mostly event-driven.
- Over-engineering state management would add complexity without user benefit.
- If removed, navigation and back-button behavior would become inconsistent.

## 6. API Integration Strategy

The frontend never talks directly to SQLite. Every data operation uses the API client wrapper.

Benefits:

- Consistent error handling.
- Centralized backend base URL selection.
- Easier maintenance if the backend host or port changes.
- Cleaner separation between presentation and persistence.

## 7. Form and Input Design

Forms should enforce data integrity before the request reaches Python. 

Validation UX Pattern (Touched/Dirty State):
- To prevent intimidating users with immediate red error boundaries and messages on page load, form validation leverages a touched/dirty state check.
- Inputs do not render `.input-invalid` borders or display text error messages until they are marked as `.touched` (triggered by `blur` or `input` events), or the form itself is marked as `.submitted` during a submission attempt.
- The submit button is immediately disabled on load if mandatory requirements are unmet, ensuring data integrity is never compromised.

Examples of Validated Fields:
- Serial number / Record ID (maps to `record_number`): `required|numbers`
- Carrier/company name (maps to `company_name`): `required|letters`
- Vehicle registration (maps to `vehicle_reg`): `required|numbers`
- Registration code (maps to `company_reg`): `numbers` (optional)

This validation is complemented by the frontend and backend mapping layers to handle compatibility transformations (e.g. auto-generating license numbers and splitting compound fields.

## 8. Dashboard Presentation

The dashboard mixes KPI cards, trend charts, and location summaries because operators need both a quick overview and a way to drill into operational risk.

Design principles:

- Put the highest-value numbers first.
- Keep charts readable and not overcrowded.
- Use caching-friendly data structures from the backend.
- Avoid forcing the user through multiple pages to answer simple status questions.

## 9. Localization Strategy

The app supports multiple languages through a local dictionary-based approach.

Why this approach was chosen:

- It is easy to audit.
- It avoids introducing a large i18n framework for a limited set of labels.
- It keeps runtime dependencies small.

Limitations:

- Complex sentence reordering is harder than in full-featured internationalization libraries.
- Translation coverage must be maintained manually.

## 10. Visual System

The visual system should remain operationally serious rather than decorative.

- Strong contrast for readability.
- Clear spacing for dense table-driven screens.
- Distinct button hierarchy for primary and destructive actions.
- Smooth but restrained transitions to avoid distraction.

## 11. Error Feedback

User-facing errors are surfaced through toast notifications, inline field messages, and confirmation modals.

Why this matters:

- The user should know whether the issue is local form validation or a backend failure.
- The UI should not silently discard submissions.
- If removed, operators would lose confidence in whether a change actually happened.

## 12. References

- [System Overview](system_overview.md)
- [System Architecture](system_architecture.md)
- [Backend Design](backend_design.md)
- [Error Handling and Validation](error_handling_and_validation.md)

## Recent UI Changes (Late May 2026)

- **Add Contract Form Refactoring:** The multi-section form has been simplified into a single "Add Contract" section. Unexposed backend fields (e.g. driver details, checkpoints) are omitted from the UI layer to streamline the transport registration flow.
- **Touched state Validation UX:** Modified validation trigger logic to prevent pre-emptive red validation error borders from rendering before a user interacts with the form.
- **Payload Mapping Adapter:** Form submissions are run through a mapping adapter inside `handleFormSubmit()` in `main_dashboard_controller.js` to ensure backward-compatibility. The adapter auto-generates `license_number` as `'LIC-' + record_number`, splits `vehicle_type_category` into `vehicle_type` and `vehicle_category`, and splits the `route` string into `route_origin` and `route_dest` before sending the POST request.

## Recent UI Changes (Early May 2026)

The frontend was updated to integrate with newly added backend features:

- **Login & Settings:** The Settings view includes a Change Password form wired to `POST /auth/change-password`. The renderer now expects and forwards an `Authorization` header for protected operations. Client networking is implemented in `frontend/js/frontend_api_client.js` and UI wiring in `frontend/js/main_dashboard_controller.js`.
- **Add Contract Address Select:** The `company_address` input on the Add Contract flow was changed to a combo/select control to support pre-populated addresses and ad-hoc entries. See [frontend/js/main_dashboard_controller.js](frontend/js/main_dashboard_controller.js).
- **License actions:** UI placeholders were added to support Renew and Suspend actions for licenses; the corresponding API calls are `POST /api/licenses/{id}/renew` and `POST /api/licenses/{id}/suspend`. Buttons and confirmation flows will be added to the license list/detail views in a follow-up.
- **Duplicate enterprise handling:** The frontend continues to post company creation requests to `POST /api/companies` and now relies on backend validation to prevent duplicates by registration number or name.

Notes:

- The renderer uses the central `frontend_api_client.js` to manage the Authorization header. Ensure that tokens returned from `POST /auth/login` are stored by the client and attached to subsequent requests.
- Address list population is left intentionally flexible — it can be populated from settings or managed by an admin interface depending on preference.

# Frontend Design

## Renderer Composition

- Entry HTML: `frontend/index.html`.
- Styling: `frontend/css/style.css`.
- API client: `frontend/js/frontend_api_client.js`.
- i18n: `frontend/js/i18n.js`.
- UI controller/router: `frontend/js/main_dashboard_controller.js`.

## Navigation Model

- Sidebar-driven single-window navigation.
- Content pane swaps page templates by route key.
- History stack supports user-level back navigation.

## Feature Views

- Dashboard (KPIs + expiring items + forecast).
- Add contract wizard (4-step guided flow).
- Search and deleted contracts views.
- Statistics page with Chart.js visualizations.
- Welcome page loaded from `frontend/pages/welcome.html`.

## Interaction Patterns

- Debounced search input to reduce unnecessary API requests.
- Modal confirm/edit interactions for destructive and update actions.
- Toast notifications for success/error feedback.
- Inline form validation with per-field error states.

## Localization and Directionality

- Supports Arabic, French, and English.
- `i18n.js` applies text replacement and RTL/LTR layout switching.
- Language state persists via local storage.

## Electron Security Bridge

- Renderer does not use Node integration.
- `electron/preload.js` exposes a minimal safe API (`getApiBase`, shortcut listener).

## Legacy Boundary

Legacy PyQt visual implementations are not part of the active frontend and are archived under `modules/legacy_pyqt_ui/`.
