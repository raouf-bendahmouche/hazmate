# Changelog — Recent Updates (Late May 2026)

This document summarizes the recent security, validation, and functionality updates made to the **Hazardous Material Transport License Management System**.

## 1. Strict Form Validation & Data Integrity Enforcement
- **9 Mandatory Fields:** Enforced strict completeness checks on the 9 target fields (Record Number, Signature/Start Date, Carrier Name, Commune Address, Vehicle Registration, Vehicle Type/Category, Route Destination, Expiry Date, and Transported Materials). If any required field is empty, the save workflow is blocked.
- **Date Chronology Constraint:** License Expiration Date must always be strictly after the Signature/Start Date. If violated, saving is disabled, the Expiration Date input highlights red, and a localized warning appears.
- **Strict Format Constraints:**
  - Registration Number and Vehicle Registration must be strictly numeric (rejecting letters).
  - Company/Carrier Name must reject numbers.
  - Company Registration (if provided) must be strictly numeric.
  - Route Destination must not be numeric-only.
- **Form Data Preservation:** On failed validation or save error, the UI never clears/resets the form, preserving all entered data and allowing non-destructive correction.
- **Double-Layer Validation:** Enforced the same strict checks in the backend business rules engine (`business_rules_engine.py`) and API schemas to guarantee database integrity.
- **PyQt UI Synchronization:** Updated the legacy PyQt data entry dialog form (`contract_data_entry_form.py`) to replicate the exact same format, required field, and date chronology validations with localized dialog warnings.
- **Automated Regression Suite:** Introduced `scripts/run_validation_tests.py` testing formatting, required field presence, date chronology, and update constraints.

## 2. Security & Access Control Enforcement
- **Enforced Authentication:** Added JWT/session token validation (`_require_auth`) across all sensitive backend write/mutation endpoints.
  - `POST /api/licenses` (Contract creation)
  - `PUT /api/licenses/{id}` (Contract updates)
  - `DELETE /api/licenses/{id}` (Contract soft deletion)
  - `POST /api/licenses/{id}/restore` (Contract restoration)
  - `POST /api/licenses/{id}/renew` (Contract renewal)
  - `POST /api/licenses/{id}/suspend` (Contract suspension)
  - `PUT /api/settings` (Application settings saving)
- **Frontend Alignment:** The Electron frontend automatically includes authorization headers on all API requests using the session token stored during sign-in.

## 3. Add Contract Simplified Flow
- **Form Simplification:** Refactored the UI from a 4-step wizard to a clean, single-section layout titled "Add Contract".
- **Fields Refactored:** Exposes only the 11 target clean fields: Record Number, Signing Date, Carrier Name, Registry Number, Address (Wilaya selector), Vehicle Reg, Vehicle Type/Category, Route Destination (single field, e.g., Setif), Expiry Date, Carrier Type, and Materials.
- **KPI and Statistics Simplification:** Removed all driver details (name/phone), total vehicles, and total drivers counters from the UI and statistics, replacing them with a "Total Contracts" count KPI card on the dashboard.
- **Touched Validation UX:** Solved the preemptive validation error rendering. Required empty inputs do not turn red or display "This field is required" error messages on load. Errors are displayed only after a user interacts with the input (blur/input) or attempts to submit the form. The submit button is disabled on page load and dynamically enabled as the form becomes valid.

## 4. Backward Compatibility Mapping Layer
- **Auto-generated Unique Keys:** The mapping layer automatically generates `license_number` as `'LIC-' + record_number` during submission to satisfy backend unique constraints.
- **Composite Field Splitting & Routing:** Compound inputs are mapped to normal tables:
  - `vehicle_type_category` is split into `vehicle_type` and `vehicle_category`.
  - `route` is mapped directly to `route_dest` (leaving `route_origin` as empty `""`). For backward compatibility with legacy route formats, if the input contains delimiters like `→`, `->`, or `-`, it is split into `route_origin` and `route_dest` automatically.
- **Bug Fix:** Fixed a mapping overwrite bug in the backend where empty/blank clean fields in requests (e.g. from legacy clients) would overwrite valid legacy fields with blank strings. Now, mappings are only performed if the clean fields have a non-empty value.

---

# Changelog — Historical Updates (Early May 2026)

- **Authentication Service:** Added `services/auth_service.py` implementing bcrypt hashing, in-memory session tokens, and password updates.
- **Auth Endpoints:** Registered `/auth/login`, `/auth/logout`, `/auth/validate`, and `/auth/change-password` routes under a factory-designed `auth_router.py`.
- **Company Duplicate Prevention:** `POST /api/companies` checks registration numbers and exact names to avoid duplicate enterprises.
- **Database Backup & Life Cycle:** Lifespan startup bootstraps the default admin credentials and starts scheduled background jobs.
