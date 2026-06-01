# Performance Optimization

## 1. Performance Goals

The application is local and data-heavy, so performance is measured by responsiveness rather than raw throughput.

Primary targets:
- Dashboard loads quickly even with thousands of contracts.
- Search remains responsive as data grows.
- Background checks do not block the UI.
- Data entry feels immediate and predictable.

## 2. Database Indexing

The most important optimization is indexing the columns used by search, expiry monitoring, and dashboard analytics.

Key indexes:
- `licenses(license_number)` for exact lookup.
- `licenses(expiration_date)` for expiry scans.
- `licenses(status)` for active/inactive filters.
- `licenses(activity_location)` for municipality analysis.
- `vehicles(registration_number)` for vehicle search.
- `vehicles(company_id)` for relational lookups.
- `companies(name)` for company search.
- `hazardous_materials(vehicle_id)` for hazmat lookups.
- `audit_logs(table_name, record_id)` for traceability queries.

Why this matters:
- The application can stay responsive without introducing external caching infrastructure.
- If indexes are removed, the main search and analytics workflows would degrade quickly as the database grows.

## 3. Statistics Caching

The dashboard statistics service uses a simple in-memory cache with a 5-minute TTL.

What it solves:
- Prevents repeated expensive aggregations on every dashboard refresh.
- Keeps the UI responsive when the user revisits the dashboard frequently.

Why not a distributed cache:
- The application is a single local desktop process.
- Redis or similar tools would add operational complexity with little benefit.

Cache invalidation strategy:
- Any mutating contract/company/vehicle operation clears the cache.
- A fresh dashboard request recomputes statistics.

## 4. Pagination Strategy

Search and listing endpoints use pagination to keep payload sizes small.

Why pagination matters:
- Large tables should not be transferred in full for ordinary browsing.
- The UI should display only a workable subset of rows at a time.
- Network payloads and rendering time remain bounded.

Recommended bounds:
- Page size capped at 50 records in the backend.
- Sorting supported server-side to avoid client-side scanning.

## 5. Lazy Rendering and UI Efficiency

The frontend should avoid rendering everything at once.

Examples:
- Only render the current view container.
- Reuse chart instances instead of rebuilding them unnecessarily.
- Debounce search input so every keystroke does not trigger a backend round trip.

## 6. Background Work Isolation

Backup creation and notification scanning run separately from request handling.

Why this matters:
- Long-running tasks should never freeze the UI.
- Expiry checks should continue even while a user is navigating or editing data.
- If background isolation were removed, the app would feel unreliable under load.

## 7. SQLite-Specific Optimizations

- Use WAL mode for improved read concurrency.
- Use busy timeout and retry logic for transient lock contention.
- Avoid heavy joins in frequently executed paths unless supported by indexes.
- Keep schema normalized enough to avoid duplication, but not so fragmented that query cost explodes.

## 8. Practical Bottlenecks

Most likely bottlenecks in this system:
- Full dashboard aggregation on large datasets.
- Search queries with many joins and filters.
- Poorly indexed text fields.
- Excessive chart rebuilds in the renderer.

## 9. What Not to Optimize Prematurely

Do not add complexity that the current runtime profile does not need.

- Do not introduce Redis for a local TTL cache.
- Do not split the backend into microservices.
- Do not replace SQLite unless concurrent multi-user writes become a real requirement.
- Do not over-abstract the UI state model before there is evidence of pain.

## 10. References

- [Database Design](database_design.md)
- [System Architecture](system_architecture.md)
- [Backend Design](backend_design.md)
# Performance Optimization

## Database-Side Optimizations

- Indexed columns for frequent lookups (license number, registration, status, location).
- WAL mode and busy timeout configured for smoother concurrent reads/writes.
- Lock retry mechanism in write helper to handle transient SQLite contention.

## Query and API Optimizations

- Search/list endpoints enforce pagination with bounded `limit` values.
- Sorting is whitelisted to safe columns to avoid expensive invalid sort patterns.
- Active/deleted views are split into dedicated query paths.

## Caching Strategy

- `Database` caches summary statistics and invalidates on mutating operations.
- `StatisticsService` caches dashboard payloads with short TTL for responsive chart rendering.

## Frontend Optimizations

- Debounced search input reduces request frequency.
- On-demand detail retrieval for edit modal and linked updates.
- Lightweight vanilla JS rendering avoids framework overhead.

## Background Work Isolation

- Backup and scheduler tasks run outside renderer flow.
- Electron waits for backend health before initial UI workload.

## Practical Tuning Guidance

- Keep `licenses` table indexed as schema evolves.
- Avoid increasing list page size beyond current API bounds without measurement.
- Review backup retention periodically to prevent local disk growth.
