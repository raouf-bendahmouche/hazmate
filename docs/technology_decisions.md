# Technology Decisions

## 1. Python

### Why it was chosen
Python is used for the backend because it is concise, easy to maintain, and well suited to business-rule heavy orchestration.

### What problem it solves
It provides a clear language for database operations, scheduling, validation, and application logic.

### Why not alternatives
- JavaScript-only backend would blur the separation between desktop UI and domain logic.
- Java or .NET would add more framework overhead for a compact local desktop system.

### Advantages
- Strong readability.
- Easy SQLite integration.
- Rich ecosystem for data processing and scheduling.

### Limitations
- Requires a Python runtime.
- Packaging needs coordination with Electron startup.

## 2. FastAPI

### Why it was chosen
FastAPI provides fast request handling and strong validation through Pydantic.

### What problem it solves
It exposes a clean local HTTP API between the Electron UI and backend services.

### Why not alternatives
- Flask is more minimal but provides less built-in validation structure.
- A custom socket protocol would be harder to maintain and debug.

### Advantages
- Clear endpoint declarations.
- Built-in request validation.
- Good async support.

### Limitations
- Requires Python packaging discipline.
- More structured than a tiny micro-framework, which is good here but still adds learning overhead.

## 3. Electron

### Why it was chosen
Electron gives the project a local desktop UI that can run cross-platform.

### What problem it solves
It lets the app behave like a native desktop product while using web technologies for the interface.

### Why not alternatives
- Pure web app would not match the local desktop requirement.
- Native desktop frameworks would require a different frontend skill set and a larger rewrite.

### Advantages
- Cross-platform.
- Good UI flexibility.
- Familiar HTML/CSS/JS development model.

### Limitations
- Larger runtime footprint.
- Requires careful process management.

## 4. SQLite

### Why it was chosen
SQLite fits a local single-user or small-team desktop application very well.

### What problem it solves
It provides persistent structured storage without needing a database server.

### Why not alternatives
- PostgreSQL or MySQL would require extra infrastructure.
- Flat files would be weaker for querying, integrity, and auditability.

### Advantages
- Zero server setup.
- ACID compliant.
- Easy backup and restore.

### Limitations
- Single-writer concurrency model.
- Not ideal for multi-user network access.

## 5. APScheduler

### Why it was chosen
It supports periodic background tasks inside the Python process.

### What problem it solves
It checks license expirations and supports time-based automation.

### Why not alternatives
- Cron would be external to the app and harder to package with the desktop workflow.

### Advantages
- Embedded scheduling.
- Easy to reason about.

### Limitations
- Only runs while the application is active.

## 6. SMTP Notifications

### Why it was chosen
SMTP is a widely supported and simple way to dispatch expiry notifications.

### What problem it solves
It allows the app to notify responsible parties about upcoming expirations.

### Why not alternatives
- External notification services would add network dependency and configuration overhead.

### Advantages
- Standard protocol.
- Easy to configure with existing mail infrastructure.

### Limitations
- Requires valid mail server credentials.
- Email delivery can fail if network or credentials are unavailable.

## 7. Chart.js

### Why it was chosen
It provides an easy way to render dashboard charts in the Electron renderer.

### What problem it solves
It visualizes statistics without requiring a heavyweight charting stack.

### Why not alternatives
- Custom canvas rendering would be too much work.
- Larger visualization libraries would add unnecessary weight.

### Advantages
- Simple integration.
- Good enough for operational charts.

### Limitations
- Not as specialized as enterprise analytics tools.

## 8. Summary

The chosen stack favors local reliability, maintainability, and clarity over infrastructure complexity. That is the correct trade-off for a desktop compliance system.