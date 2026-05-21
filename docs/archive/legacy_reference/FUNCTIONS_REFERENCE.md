# Functions Reference

This reference outlines the critical functions within the application, split across the Electron (Main Process) and Python (Flask Backend) environments.

## Electron (`electron/main.js`)

### `findPython()`
- **Input**: None.
- **Output**: `String` - Absolute path to the Python executable.
- **Purpose**: Determine the correct Python executable to use for the host operating system.
- **Flow**: Checks `process.platform`. If Windows, it looks for `.venv/Scripts/python.exe`. If Linux/macOS, it looks for `.venv/bin/python3`. If the virtual environment does not exist, it falls back to the system's global `python` or `python3` command.

### `startPythonServer()`
- **Input**: None.
- **Output**: None (Spawns a child process).
- **Purpose**: Bootstraps the Flask backend API.
- **Flow**: Calls `findPython()` to get the executable path. Uses Node's `child_process.spawn` to execute `api/server.py` using that Python path. Attaches event listeners to log the Python process's `stdout` and `stderr` to the Electron console.

### `isServerReachable(timeout)`
- **Input**: `timeout` (Integer) - Maximum time in milliseconds to wait for a response (Default: 800ms).
- **Output**: `Promise<Boolean>` - True if the server responded with HTTP 200, false otherwise.
- **Purpose**: A quick ping to verify if the Flask server is currently awake and responding.
- **Flow**: Makes an HTTP GET request to `http://127.0.0.1:5757/api/ping`. If a 200 OK is received before the timeout, it resolves `true`. If a connection error occurs or the request times out, it resolves `false`.

### `waitForServer(retries, delay)`
- **Input**: `retries` (Integer) - Number of attempts (Default: 30), `delay` (Integer) - Milliseconds between attempts (Default: 500ms).
- **Output**: `Promise<void>` - Resolves when the server is ready, rejects if retries run out.
- **Purpose**: A blocking wait mechanism utilized during app startup to ensure the UI isn't shown before the backend is ready to serve data.
- **Flow**: Recursively attempts to hit `/api/ping`. On success, resolves immediately. On failure, waits `delay` ms and tries again until `retries` hits 0, at which point it throws an error.

### `createWindow()`
- **Input**: None.
- **Output**: None (Creates UI window).
- **Purpose**: Instantiates and displays the main Electron application window.
- **Flow**: Creates a `BrowserWindow` object with specified dimensions and security settings (enabling `preload.js` and disabling `nodeIntegration`). Loads the primary `index.html` file into the window.

---

## Python Backend (`api/server.py`)

### Flask App Initialization
- **Components**: `app = Flask(__name__)`, `CORS(app)`
- **Purpose**: Bootstraps the HTTP server environment and enables Cross-Origin Resource Sharing (CORS) so the local Electron UI can seamlessly request data without browser security blocks.

### `ping()` -> `@app.route("/api/ping")`
- **Input**: HTTP GET request.
- **Output**: JSON payload `{"status": "success", "message": "pong"}`.
- **Purpose**: Health check endpoint.
- **Flow**: Immediately returns an HTTP 200 response. Exclusively used by Electron's `isServerReachable()` and `waitForServer()` to confirm backend readiness.

### `list_licenses()` -> `@app.route("/api/licenses")`
- **Input**: URL Query Parameters (`search`, `status`, `page`, `limit`, etc.).
- **Output**: JSON payload containing an array of license records and pagination metadata.
- **Purpose**: Fetches a filtered, sorted, and paginated list of licenses.
- **Flow**: Extracts query parameters from the Flask `request` object. Passes these arguments to `db.search_licenses()`. Wraps the resulting data in a success JSON structure and returns it.

### `create_license()` -> `@app.route("/api/licenses", methods=["POST"])`
- **Input**: JSON HTTP POST body containing license, company, and vehicle details.
- **Output**: JSON payload with the new `license_id` and HTTP 201 Created status.
- **Purpose**: Persists a new transport license, automatically linking or creating associated companies and vehicles.
- **Flow**: 
  1. Validates required fields (`company_name`, `vehicle_reg`, etc.).
  2. Checks for duplicate license numbers.
  3. Queries the database to find an existing Company by registration. If not found, creates a new Company record.
  4. Queries for an existing Vehicle. If not found, creates a new Vehicle record linked to the Company.
  5. Inserts Route and Hazmat details if provided.
  6. Finally inserts the License record linked to the Vehicle and Route.

### Database Init (`db = Database()`)
- **Purpose**: Instantiates the primary connection to the SQLite database.
- **Flow**: Creates the `db` object which automatically handles table creation and schema validation on startup, acting as the Single Source of Truth for data access.
