# Changelog

All notable changes to the Hazmat Transport License Management System.

---

## [2.1.0] — 2026-05-29

### Added

#### ⚙️ Settings Page
- Full settings page accessible from sidebar (⚙️ nav item) and topbar (gear icon)
- **Change Password** — form with current/new/confirm fields, calls `/auth/change-password` API
- **Theme Toggle** — Light/Dark mode buttons with instant visual switch
- **Language Selector** — Arabic 🇩🇿 / French 🇫🇷 / English 🇬🇧 with instant interface update
- **Account Info** — displays username, role, and app version
- **Logout** — invalidates session token and redirects to login
- Settings page styled with responsive 2-column card grid layout
- 17 new translation keys per language (EN/FR/AR) for the settings page

#### 🚚 Vehicle & Driver Table Management
- New **table-based display** for vehicles and drivers inside contracts
- Each row shows item details with **Edit ✏️** and **Delete 🗑️** buttons
- **Mini-modal popups** for adding/editing individual vehicles or drivers
- **Duplicate registration validation** within the same contract
- In-memory array architecture (`_formVehicles`, `_formDrivers`) as single source of truth
- Card-based section layout with header (title + "Add" button) and table body
- 11 new translation keys per language (EN/FR/AR) for management buttons and modals

#### 🔍 Search Page Action Toolbar
- **Add Contract** button (➕) — navigates to add-contract page
- **Edit Contract** button (✏️) — opens edit modal for selected row
- Buttons placed in a dedicated `action-toolbar` div between search filters and results table
- Search/Reset buttons remain inside the filter card where they logically belong

### Changed
- Edit modal width increased from 580px → 720px to accommodate vehicle/driver tables
- `renderAddContract()` now resets in-memory vehicle/driver arrays on entry
- `openEditModal()` populates in-memory arrays from API data before rendering
- `handleFormSubmit()` reads from in-memory arrays instead of DOM scraping
- Sidebar footer now contains the Settings nav item (was previously empty)

### Removed
- `addVehicleRow()` function — replaced by table + mini-modal system
- `addDriverRow()` function — replaced by table + mini-modal system
- Old `.vehicle-item-row` / `.driver-item-row` CSS classes
- Inline form row duplication approach for multi-item management

---

## [2.0.0] — 2026-05-28

### Initial Features
- Electron desktop application with FastAPI backend
- SQLite database with bcrypt authentication
- Dashboard with statistics and charts
- Contract CRUD operations (add, search, edit, delete, restore)
- Multi-language support (Arabic, French, English)
- Dark/Light theme toggle
- Company address selection from Setif communes
- Hazardous material type classification
- Vehicle type and category management
- Driver management
- License expiry tracking and notifications
- Deleted contracts archive with restore capability
- Advanced statistics page with Chart.js visualizations
