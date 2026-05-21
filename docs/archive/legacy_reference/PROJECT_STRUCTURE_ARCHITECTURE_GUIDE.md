# 🏗️ PROJECT STRUCTURE & ARCHITECTURE GUIDE

Welcome to the definitive architectural and structural guide for the **Hazardous Material Transport License Management System**.

As a senior engineer, I have designed this document to give you a complete mental model of the system. We will explore every layer, understand _why_ decisions were made, and learn how to navigate and extend this system confidently.

---

## 🧠 1. MENTAL MODEL: How to Think About This System

Think of this system as **"Two Apps in a Trench Coat"** packaged into a single desktop application.

Initially, this project started as a Python `PyQt5` desktop application (as seen in legacy documentation). However, it has evolved into a **hybrid web-technology desktop app** using **Electron**.

1. **The Backend (Flask/Python)**: Runs a local HTTP REST API and manages the SQLite database.
2. **The Frontend (Electron/HTML/JS)**: A Chromium-based browser window that renders the UI and makes HTTP calls to the local Flask API.

They are glued together by Electron's Main Process, which automatically starts the Python server in the background before opening the UI.

---

# 📂 2. FULL PROJECT STRUCTURE (RECURSIVE)

```text
/home/raouf/Desktop/lastversion-source/
├── 📁 api/
│   └── 📄 server.py
├── 📁 db/
│   ├── 📄 database.py
│   ├── 📄 schema.sql
│   └── 📄 licenses.db
├── 📁 docs/
│   └── 📄 FILE_STRUCTURE.md
├── 📁 electron/
│   ├── 📄 main.js
│   └── 📄 preload.js
├── 📁 node_modules/
├── 📁 notifications/
│   ├── 📄 email.py
│   └── 📄 scheduler.py
├── 📁 ui/
├── 📄 main.py
├── 📄 add_test_data.py
├── 📄 build.bat
├── 📄 package.json
├── 📄 requirements.txt
├── 📄 TECHNICAL_DOCUMENTATION.md
├── 📄 USER_MANUAL.md
└── 📄 TRAINING_GUIDE.md
```

---

# 📁 3. DIRECTORY ANALYSIS

## 📁 `/electron`

### 🎯 Purpose

Acts as the OS-level wrapper for the application. It creates the desktop window and bridges the gap between the OS, the Python backend, and the UI.

### 📦 What It Contains

`main.js` (Main Process), `preload.js` (Context Bridge).

### 🧠 Why It Exists

Web browsers cannot natively run Python background tasks or read local files without restriction. Electron provides a Node.js runtime to spawn the Flask API and a Chromium runtime to display the UI securely.

### 🏗️ Architectural Role

Infrastructure / Host Environment.

### 🔗 Interactions

Spawns `/api/server.py` as a child process. Loads `/ui/index.html`.

### ⚠️ If You Ignore It

You won't understand how the app starts, how the backend is booted, or how IPC (Inter-Process Communication) security works.

### 📊 Importance Level

**Critical**

### 🎓 Learning Value

High. Teaches you how to package cross-language (Node.js + Python) applications.

## 📁 `/api`

### 🎯 Purpose

The backend brain. Serves data to the frontend via a RESTful API.

### 📦 What It Contains

`server.py` and API route definitions.

### 🧠 Why It Exists

Decouples the database logic from the UI. By using a REST API, the frontend simply fetches data, allowing the frontend technology (Electron/React/Vanilla) to be easily swapped in the future.

### 🏗️ Architectural Role

Backend / Controller Layer.

### 🔗 Interactions

Receives HTTP requests from `/ui`, queries `/db/database.py`, and returns JSON.

### ⚠️ If You Ignore It

You will have no idea how business rules (like contract validation) are enforced.

### 📊 Importance Level

**Critical**

## 📁 `/db`

### 🎯 Purpose

Handles all data persistence and SQLite interactions.

### 📦 What It Contains

`database.py` (CRUD operations), `schema.sql` (Table definitions), and `licenses.db` (The actual SQLite database file).

### 🧠 Why It Exists

Separation of concerns. The API layer should not write raw SQL. This folder abstracts SQL behind Python methods.

### 🏗️ Architectural Role

Data Access Layer (DAL).

### 🔗 Interactions

Provides methods to `/api/server.py`.

### ⚠️ If You Ignore It

You won't understand the data model or how relational links (e.g., Company -> Vehicle -> License) function.

### 📊 Importance Level

**Critical**

## 📁 `/ui`

### 🎯 Purpose

The visual presentation layer.

### 📦 What It Contains

HTML, CSS, JavaScript files for the dashboard, forms, and charts.

### 🧠 Why It Exists

To provide a user-friendly interface for non-technical operators to manage hazardous material licenses.

### 🏗️ Architectural Role

Frontend (Renderer).

### 🔗 Interactions

Calls `/api` endpoints. Uses `window.api` exposed by `/electron/preload.js`.

### 📊 Importance Level

**Critical**

## 📁 `/notifications`

### 🎯 Purpose

Background worker queue.

### 📦 What It Contains

`scheduler.py` and `email.py`.

### 🧠 Why It Exists

Emailing and checking 10,000 records for expiration dates is slow. If we did this on the main API thread, the UI would freeze. This folder runs these tasks asynchronously.

### 🏗️ Architectural Role

Background Services.

### 🔗 Interactions

Reads from `/db`, connects to external SMTP servers.

### 📊 Importance Level

**Important**

---

# 📄 4. FILE ANALYSIS (DEEP DIVE)

## 📄 `main.py`

### 🎯 Purpose

A fallback entry point script that routes Python execution to npm.

### ⚙️ Responsibilities

Detects the OS (`win32` vs Linux/Mac) and runs `npm start` via Python's `subprocess` module.

### 🧠 Why It Exists

Legacy developers or automated build pipelines might be used to running `python main.py` to start the app. This file intercepts that habit and correctly boots the new Electron stack.

### 🔗 Dependencies

`os`, `subprocess`, `sys`, `platform`.

### ⚠️ If Deleted

`python main.py` will fail, but developers can still properly start the app using `npm start`.

### 📊 Importance Level

**Optional** (Over-engineered crutch).

### 🎓 Should You Study It?

**SKIP**. It's just a 15-line process wrapper.

## 📄 `add_test_data.py`

### 🎯 Purpose

Database seeder. Generates ~500 realistic, relational fake records for testing.

### ⚙️ Responsibilities

1. Initializes DB connection.
2. Generates dummy Companies.
3. Generates dummy Vehicles attached to Companies.
4. Generates fake Licenses with randomized dates (Active, Expiring, Expired).

### 🧠 Why It Exists

Testing an empty dashboard is impossible. This script populates the charts, tables, and search functionalities so developers can verify UI logic without manual data entry.

### 🔗 Dependencies

`db.database.Database`, `datetime`, `random`.

### 📥 Inputs / Outputs

Input: Execution command. Output: `licenses.db` filled with rows.

### ⚠️ If Deleted

QA testing becomes incredibly tedious.

### 📊 Importance Level

**Important**

### 🎓 Should You Study It?

**YES**. It shows exactly how the Python Database API is meant to be consumed by the backend.

## 📄 `electron/main.js` & `electron/preload.js`

### 🎯 Purpose

`main.js` is the backend OS wrapper; `preload.js` is the security bouncer.

### ⚙️ Responsibilities

`main.js` spawns the Flask server. `preload.js` exposes isolated IPC (Inter-Process Communication) channels.

### 🧠 Why It Exists

If you allow a web UI to have direct access to Node.js filesystem APIs (`nodeIntegration: true`), a malicious script could wipe the user's hard drive. `preload.js` prevents this.

### ⚠️ If Deleted

The app physically cannot open a window or communicate securely.

### 📊 Importance Level

**Critical**

---

# 💻 5. CODE EXPLANATION (DEEP)

Let's look at the architectural patterns found in the codebase.

## The Entry Pattern (`main.py`)

```python
def main():
    app_path = os.path.dirname(__file__)
    try:
        if sys.platform == "win32":
            subprocess.run(["npm.cmd", "start"], cwd=app_path, check=True)
        else:
            subprocess.run(["npm", "start"], cwd=app_path, check=True)
```

- **What it does:** Uses `subprocess.run` to execute a shell command.
- **Why written this way:** `npm` on Windows is technically a `.cmd` batch file (`npm.cmd`). Failing to specify `.cmd` on Windows subprocess calls often results in a `FileNotFoundError`.

## The Seeding Pattern (`add_test_data.py`)

```python
for comp_idx, company_name in enumerate(company_names):
    try:
        company_id = db.add_company(name, reg_num, address, type, acc_type)
        # ... Nested vehicle creation ...
```

- **What it does:** Loops through dummy arrays to create relational data.
- **Pattern:** **Data Access Object (DAO) Pattern**. Notice it calls `db.add_company()`, not raw `INSERT INTO` statements. The `Database` class acts as the DAO, hiding SQL syntax from the application layer.

---

# 🔄 6. SYSTEM FLOWS

## 🛒 Contract/License Addition Flow

1. **Frontend (UI):** User fills out the "Add Contract" HTML form. Live validation checks for numericality/alphabetical rules.
2. **Submission:** JS intercepts the form submit and sends a `POST` fetch request to `http://localhost:5757/api/licenses`.
3. **Backend (API):** `/api/server.py` receives the JSON payload. It acts as a guard, validating inputs again (Defense in Depth).
4. **Database (DB):** `server.py` calls `db.add_license()`. SQLite opens a transaction, writes the data to the WAL (Write-Ahead Log), commits, and closes.
5. **Response:** Flask returns a `201 Created` JSON response. UI shows a green success toast.

## 🔐 Security / Authorization Flow

- _Note: This is a local desktop application. There is no traditional JWT or Session-based network authentication._
- **OS Level Security:** Access to the app relies on Windows OS user accounts.
- **Data Level Security:** SQLite prevents unauthorized network access because it only listens to local file reads by the Flask instance running on `localhost`.

## 🌐 Language Flow (i18n)

1. **State:** Language preference (EN/FR/AR) is stored in the `settings` SQLite table.
2. **Initialization:** On boot, Flask sends the current language to the UI.
3. **Frontend Application:**
   - A JSON dictionary maps keys (e.g., `ADD_CONTRACT`) to translated strings.
   - If AR is selected, the HTML `<body>` gets `dir="rtl"` applied via DOM manipulation, instantly flipping the entire application layout to Right-To-Left.

---

# 🧠 7. SYSTEM DESIGN & ARCHITECTURE

## The Architecture: Local Modular Monolith (Hybrid Web)

This system utilizes a **Client-Server architecture running entirely on a single machine**.

- **Why this architecture?**
  - Desktop environments are safe and isolated. Transportation companies often work offline or have poor internet in logistical hubs.
  - Using Web Technologies (Electron/Flask) instead of Native UI (PyQt5) makes it vastly easier to draw complex statistical charts (using tools like Chart.js or D3) and makes the UI responsive.

## Separation of Concerns (SOLID)

- **Single Responsibility:** `email.py` only sends emails. `database.py` only talks to SQLite. `server.py` only routes HTTP traffic.
- **Open/Closed:** The database class can be extended with new queries without modifying existing ones.

---

# 🗄️ 8. DATABASE MAPPING

Database Engine: **SQLite 3**

| Table                 | Purpose                                            | Relationships                                                              |
| --------------------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| `companies`           | Stores transport company data.                     | 1-to-Many with `vehicles`                                                  |
| `vehicles`            | Stores truck/van plates.                           | Belongs to `companies`. 1-to-Many with `licenses`.                         |
| `routes`              | Origin/Destination logic.                          | Referenced by `licenses`.                                                  |
| `licenses`            | **The Core Entity.** The legal transport contract. | Foreign Keys to `vehicles` and `routes`.                                   |
| `hazardous_materials` | Defines what dangerous goods are carried.          | Belongs to `vehicles`. (Quantity column was removed per April 2026 specs). |
| `settings`            | Key/Value store for app configs (SMTP, i18n).      | None.                                                                      |
| `notifications_log`   | Audit trail for sent emails.                       | Belongs to `licenses`.                                                     |

**Key Architecture Decision:** `PRAGMA journal_mode=WAL` (Write-Ahead Logging).

- _Why?_ SQLite natively locks the _entire database_ on write. In a system with background workers reading the DB for expiring licenses while a user is writing a new contract, database locks crash the app. WAL allows simultaneous readers and writers.

---

# ⚡ 9. PERFORMANCE ANALYSIS

- **Where caching happens:** Global UI aggregates (like Total Vehicles) are cached in the Flask layer or queried via highly optimized SQL aggregates (`COUNT()`).
- **Why Redis is NOT used:** This is a local desktop application. Introducing Redis would require the user to install a Redis server on Windows, which is a massive deployment nightmare. SQLite is serverless and perfectly capable of handling sub-second queries for 100,000+ rows.
- **Indexing:** The schema specifically indexes `expiration_date` and `status` because the background scheduler constantly queries these columns to find expiring contracts.

---

# 🔐 10. SECURITY ANALYSIS

1.  **Frontend Strict Validation:** As of April 2026, the UI blocks letters in number fields _live_ to prevent bad data.
2.  **Backend Guard Checks:** Even if the UI is bypassed, the Flask API re-validates types and lengths.
3.  **SQL Injection:** Addressed via Parameterized Queries. You will see `execute("INSERT INTO... VALUES (?, ?)", (val1, val2))` instead of string concatenation.
4.  **No `nodeIntegration`:** The Electron Renderer has node capabilities stripped to prevent XSS attacks from accessing the user's filesystem.

---

# ❌ 11. COMMON MISTAKES & BAD DESIGN ALTERNATIVES

- **Mistake:** Storing licenses and vehicles in a single flat table.
  - _Why it's bad:_ Data duplication. If a vehicle plate changes, you would have to update 500 license rows instead of 1 vehicle row.
- **Mistake:** Soft-deleting by adding an `is_deleted` column to the active query everywhere.
  - _Why it's better here:_ The API created a _dedicated_ `/api/licenses/deleted` route. This prevents active business logic from accidentally loading deleted data.
- **Mistake:** Leaving legacy `main.py` wrappers.
  - _Why it's bad:_ Creates confusion about how to start the app.

---

# 🔍 12. EXTRA REQUIREMENTS

## 1. Dead Code & Over-engineering

- **`main.py`:** Pure over-engineering. It's a Python script that runs an NPM script that runs Electron that runs a Python script. It should be deleted, and documentation updated to solely use `npm start`.
- **`build.bat`:** Uses `PyInstaller`. This suggests it is either a legacy artifact from the PyQt5 days OR it is now used exclusively to compile the Flask backend into an `.exe` before Electron packages the whole thing. If the latter, it is poorly named.

## 2. Suggested Improvements

- **TypeScript Migration:** Move from vanilla JavaScript to TypeScript for the Electron UI to match the strict type validation happening in Python.
- **ORM Integration:** The `database.py` likely uses raw SQL. Integrating `SQLAlchemy` would make complex querying (like the new Carrier Intelligence municipality slices) much cleaner.

## 3. Complexity Analysis

- **Easiest Part:** `settings` and i18n. It's a simple dictionary swap.
- **Hardest Part:** The Electron-to-Flask lifecycle. Managing child processes, ensuring the Python server dies when the Electron app is closed (preventing zombie processes and ghost ports), and handling race conditions on boot.

---

# 🎓 13. LEARNING ROADMAP

To master this codebase, follow this step-by-step plan:

### Step 1: Understand the Data Model (Day 1)

- **Study:** `/db/schema.sql` and `add_test_data.py`.
- **Goal:** Understand how the entities relate. If you don't understand the DB, you won't understand the API.

### Step 2: Master the Backend API (Day 2)

- **Study:** `/api/server.py` and `/db/database.py`.
- **Goal:** Learn how Flask accepts a request, passes it to the DB class, and returns JSON. Look closely at the `/api/licenses/deleted` endpoint.

### Step 3: Explore the UI & API Consumption (Day 3)

- **Study:** `/ui` (HTML/JS files).
- **Goal:** See how the frontend fetches data and renders charts. Understand the strict live validation logic.

### Step 4: The Infrastructure Wrapper (Day 4)

- **Study:** `/electron/main.js` and `package.json`.
- **Goal:** Learn how the system orchestrates booting multiple languages and servers simultaneously.

### 🚫 What to Skip Initially:

- `build.bat`
- `/node_modules/`
- Deep dive into charting libraries. Focus on the data pipeline first.
