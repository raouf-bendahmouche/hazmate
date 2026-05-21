# Project Overview

## Hazardous Material Transport License Management System

The **Hazardous Material Transport License Management System** is a robust cross-platform desktop application designed to modernize, digitize, and effectively manage hazardous material transport operations. The system helps in tracking driver licenses, vehicle records, transport routes, and crucial compliance metrics.

### Key Features
- **License Management**: Add, update, and monitor transport licenses.
- **Company & Vehicle Tracking**: Track companies, transport carriers, and individual vehicles securely.
- **Statistics & Dashboard**: Comprehensive dashboard showing expiring licenses and monthly transport statistics.
- **Notifications**: Automated tracking of licenses nearing expiration.

## Application Architecture

The system follows a decoupled architecture, dividing responsibilities between a modern frontend desktop container and a powerful backend data server. 

- **Frontend (Electron)**: Built with Node.js and Electron, the frontend provides a secure, locally-hosted window to display the user interface. It acts exclusively as a view layer and does not handle database connections directly.
- **Backend (Python Flask)**: A lightweight Python API server that manages all heavy business logic. It handles the database (SQLite), processes API requests, calculates statistics, and manages automated background tasks like expiration tracking.
- **Database (SQLite)**: A local database file is utilized via Python's database layers, ensuring the application is fully portable and doesn't require a heavy standalone database server like MySQL or PostgreSQL.

### System Flow Diagram

```text
[ User Interaction ] 
        |
        v
+-------------------------------+
|  Electron Renderer (UI)       |  <-- (HTML/CSS/JS Display)
|  (Localhost Web Frontend)     |
+-------------------------------+
        |
        | HTTP/REST via Axios/Fetch
        v
+-------------------------------+
|  Python Flask (Backend API)   |  <-- (Port 5757)
|  Handles Business Logic       |
+-------------------------------+
        |
        | SQL Queries
        v
+-------------------------------+
|  SQLite Database              |  <-- (db/ local files)
+-------------------------------+
```

### Why this architecture?
By separating the UI (Electron) from the business logic (Python Flask):
1. **Performance**: Heavy database operations or long-running background tasks (like license expiration scheduling) don't freeze the UI thread.
2. **Ecosystem**: Python possesses a rich ecosystem for data management and task scheduling, while Node.js/Electron is exceptional for rendering beautiful desktop UIs cross-platform.
3. **Portability**: It effectively packages a full client-server model into a single desktop application easily deployable on Windows and Linux.
