# File Structure

This document details the critical files and directories within the Hazardous Material Transport License Management System, explaining their purpose and functionality.

## Root Directory

### `main.py`
- **Purpose**: Python entry point.
- **What it does**: A simple fallback entry point that attempts to run `npm start` utilizing Python's `subprocess`.
- **Why it exists**: Provides an alternative starting mechanism if the user attempts to run the project via Python rather than npm, routing them to the correct Electron start sequence.

### `package.json`
- **Purpose**: Node.js and Electron configuration file.
- **What it does**: Declares the application name, version, and dependencies (like Electron). It also defines the critical `start` script (`electron . --no-sandbox`) to launch the application.
- **Why it exists**: Required by Node.js to manage packages and scripts, and by Electron to determine the main entry file (`electron/main.js`).

### `requirements.txt`
- **Purpose**: Python dependency list.
- **What it does**: Lists all the necessary pip packages (e.g., `Flask`, `Flask-CORS`) required for the backend to function.
- **Why it exists**: Ensures developers and environments install the exact Python dependencies needed for the Flask server.

## `/electron/` (Frontend Architecture)

### `electron/main.js`
- **Purpose**: Electron Main Process script.
- **What it does**: This is the core orchestrator of the application. It discovers the correct Python environment (Windows or Linux), spawns the Flask backend as a child process (`spawn(python, ['api/server.py'])`), waits for the backend to be healthy via HTTP ping, and then opens the main `BrowserWindow` to display the UI.
- **Why it exists**: To control the desktop application's lifecycle, manage native operating system interactions, and handle the crucial startup sequence of the backend.

### `electron/preload.js`
- **Purpose**: Secure Context Bridge script.
- **What it does**: Exposes a safe, restricted subset of Node.js and Electron IPC (Inter-Process Communication) functionalities to the web frontend (Renderer). 
- **Why it exists**: Enforces security by keeping `nodeIntegration` disabled in the Renderer, ensuring the UI cannot directly run arbitrary system commands, while still allowing it to request data (like the API base URL) from the Main Process.

## `/api/` (Backend Architecture)

### `api/server.py`
- **Purpose**: Flask Backend API.
- **What it does**: Initializes the Flask HTTP server on port 5757. It connects to the database and defines all the RESTful API routes (`/api/licenses`, `/api/companies`, etc.) that the frontend consumes. It also starts background schedulers.
- **Why it exists**: To act as the centralized logic controller, ensuring data is safely validated and processed before being written to or read from the database.

## Other Key Directories

### `/ui/`
- **Purpose**: Frontend Assets.
- **What it does**: Contains the HTML, CSS, and JavaScript files that make up the visual user interface loaded by the Electron Renderer.
- **Why it exists**: Keeps the presentation layer completely separate from the backend logic and main process orchestrator.

### `/db/`
- **Purpose**: Database Layer.
- **What it does**: Contains Python modules responsible for raw SQLite database interactions (CRUD operations), schema migrations, and storing the local `.db` files.
- **Why it exists**: Abstracts raw SQL queries away from the Flask routing layer, maintaining clean, modular architecture.

### `/notifications/`
- **Purpose**: Automated Task Layer.
- **What it does**: Houses scripts like `scheduler.py` which run in background threads to periodically check for expiring licenses and trigger notifications.
- **Why it exists**: To decouple long-running or periodic background tasks from the immediate request/response cycle of the main Flask API.
