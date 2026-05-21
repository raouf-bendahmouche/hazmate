# Deployment and Runtime

## 1. Deployment Model

This project is intentionally local desktop only. It is not deployed as a cloud service and does not require a remote application server for normal use.

## 2. Runtime Prerequisites

- Node.js and npm for Electron.
- Python 3.x for the backend process.
- A local writable filesystem for the SQLite database and backups.

## 3. Local Setup

### Linux/macOS

1. Install Node dependencies with `npm install`.
2. Create a virtual environment with `python3 -m venv .venv`.
3. Install Python dependencies with `.venv/bin/python -m pip install -r requirements.txt`.
4. Start the application with `npm start`.

### Windows

1. Run `npm install`.
2. Create `.venv` with `py -3 -m venv .venv`.
3. Install backend dependencies with `.venv\Scripts\python -m pip install -r requirements.txt`.
4. Launch with `npm start`.

## 4. Startup Sequence

1. Electron launches from the root `package.json` script.
2. The main process checks whether the FastAPI backend is already reachable.
3. If not, it spawns Python and runs `backend/api/api_endpoint_manager.py`.
4. Electron waits for `/api/ping` to succeed.
5. The frontend is loaded into the BrowserWindow.

Why this design works:
- Users do not need to start two processes manually.
- The app can recover gracefully if the backend is not already active.
- The UI only opens after the API is ready.

## 5. Shutdown Behavior

- Closing the Electron window terminates the desktop session.
- FastAPI lifespan hooks stop the scheduler and background manager.
- SQLite data remains on disk in `database/licenses.db`.

Why this matters:
- The application should shut down cleanly without corrupting data.

## 6. Database Locations

- Main database: `database/licenses.db`.
- Backups: `database/backups/`.

## 7. Backup Behavior

The background job manager writes timestamped database copies.

Why this matters:
- The system needs a simple local recovery path.
- Copy-based backups are easy to verify and restore.

## 8. Packaging Notes

The repository includes Electron startup scripts and historical packaging files, but the canonical development workflow is still `npm start` from the workspace root.

## 9. Operational Checks

Before considering the app ready, verify:
- The backend starts and responds to `/api/ping`.
- The dashboard loads.
- Search returns data.
- Create/update/delete flows work.
- Statistics render without errors.

## 10. References

- [System Overview](system_overview.md)
- [System Architecture](system_architecture.md)
- [Project Cleanup and Refactor Log](project_cleanup_and_refactor_log.md)