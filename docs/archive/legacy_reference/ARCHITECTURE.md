# System Architecture

The application is built on a split-stack architecture, utilizing Electron for the desktop frontend and Python (Flask) for the backend data operations.

## High-Level System Diagram

```text
+-------------------------------------------------------------+
|                     User Desktop OS                         |
|                                                             |
|  +---------------------------+  +------------------------+  |
|  |     Electron Process      |  |     Python Process     |  |
|  |                           |  |                        |  |
|  |  [Renderer] (UI Window)   |  |   [Flask Server]       |  |
|  |  HTML, CSS, JS (Axios)    |  |   Port: 5757           |  |
|  |           |               |  |           |            |  |
|  |           | (IPC Bridge)  |  |           |            |  |
|  |           v               |  |           v            |  |
|  |  [Main] (Node.js)         |  |   [Data & Logic]       |  |
|  |  Spawns Python Subprocess |  |   db/, notifications/  |  |
|  +---------------------------+  +------------------------+  |
|              |                              |               |
|              +---------> HTTP/REST <--------+               |
+-------------------------------------------------------------+
```

## Communication Flows

### 1. Inter-Process Communication (IPC) Flow
The Electron environment consists of two main pieces: the **Main Process** (Node.js) and the **Renderer Process** (Chromium Web UI). 
For security, the Renderer does not have access to the Node.js file system. Instead, they communicate via IPC through the `preload.js` bridge.

**Flow Example:**
1. UI (`index.html`) needs to know where the Flask API is located.
2. UI calls `window.api.getBaseUrl()`.
3. `preload.js` securely catches this and translates it to an IPC event: `ipcRenderer.invoke('get-api-base')`.
4. The Main Process (`main.js`) hears `'get-api-base'` and returns `http://127.0.0.1:5757`.
5. The UI receives the URL and uses it for subsequent HTTP requests.

### 2. Electron ↔ Flask Flow (Startup)
1. User runs `npm start`.
2. `electron/main.js` wakes up.
3. It determines the user's OS and locates the Python virtual environment.
4. It calls `spawn()` to launch `api/server.py` in the background.
5. It repeatedly pings `http://127.0.0.1:5757/api/ping` until it gets a 200 OK.
6. Once the Flask server replies, Electron opens the visual UI window.

### 3. HTTP API Communication Flow
Once the UI is visible and the Flask backend is running, all data operations happen via standard REST API calls.

**Flow Example (Fetching Licenses):**
1. User clicks "View Licenses" in the UI.
2. UI JavaScript fires an HTTP GET request to `http://127.0.0.1:5757/api/licenses`.
3. The Flask server (`server.py`) receives the request.
4. Flask asks the `Database` class (`db/database.py`) to execute a `SELECT` query on the SQLite DB.
5. SQLite returns the data to Flask.
6. Flask formats the data as JSON and returns an HTTP 200 response to the UI.
7. The UI parses the JSON and renders the table.
