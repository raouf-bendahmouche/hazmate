# Technology Decisions: Tools & Rationale

## 1. Core Framework: Electron
### Why it was chosen:
- **Requirement**: The application must run as a local desktop software without internet dependency.
- **Problem Solved**: Cross-platform desktop compatibility using web technologies (HTML/CSS/JS).
- **Advantages**: Access to native OS features, automatic updates, and a large community.
- **Alternatives**: Qt (C++), JavaFX. Chosen Electron for rapid development and flexibility in UI design.
- **Limitations**: Higher memory consumption compared to native C++ apps.

## 2. Backend Language: Python
### Why it was chosen:
- **Requirement**: Robust data processing and complex business logic handling.
- **Problem Solved**: Ease of implementing background jobs, scheduling, and database orchestration.
- **Advantages**: Readable syntax, vast ecosystem of libraries (Pydantic, Uvicorn), and excellent for rapid engineering.
- **Alternatives**: Node.js, Go. Python was chosen for its dominance in data-heavy and logic-heavy engineering tasks.
- **Limitations**: Global Interpreter Lock (GIL) can limit true parallelism (not an issue for this scale).

## 3. Web Framework: FastAPI
### Why it was chosen:
- **Requirement**: High-performance, modern REST API.
- **Problem Solved**: Automatic request validation, OpenAPI documentation, and asynchronous support.
- **Advantages**: Extremely fast (comparable to Node.js and Go), easy to test, and reduces boilerplate code.
- **Alternatives**: Flask, Django. FastAPI is more modern and provides better validation out-of-the-box.
- **Limitations**: Relatively newer compared to Flask, but with a rapidly growing ecosystem.

## 4. Database: SQLite
### Why it was chosen:
- **Requirement**: Zero-configuration, local persistence.
- **Problem Solved**: Eliminates the need for a separate database server (PostgreSQL/MySQL), simplifying local installation.
- **Advantages**: Single-file storage makes backups trivial; high performance for single-user desktop apps.
- **Alternatives**: PostgreSQL, MongoDB. SQLite is the industry standard for local data storage.
- **Limitations**: Not suitable for high-concurrency multi-user environments (not the use case here).

## 5. UI Logic: Vanilla JavaScript
### Why it was chosen:
- **Requirement**: Lightweight, responsive UI without heavy dependencies.
- **Problem Solved**: Rapid rendering and direct DOM manipulation.
- **Advantages**: Zero build time, complete control over the UI lifecycle, and no framework overhead.
- **Alternatives**: React, Vue, Angular. Chose Vanilla JS to maintain simplicity and performance for a local desktop tool.
- **Limitations**: State management can become complex for very large applications (mitigated by a modular controller).

## 6. Validation: Pydantic
### Why it was chosen:
- **Requirement**: Strict data validation.
- **Problem Solved**: Ensures the backend only processes valid, well-structured data.
- **Advantages**: High speed, integration with FastAPI, and clear error messages.
- **Alternatives**: Marshmallow, Cerberus. Pydantic is currently the gold standard for Python validation.
- **Limitations**: Minor performance overhead (optimized in Pydantic v2).
