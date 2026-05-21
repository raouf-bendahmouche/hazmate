## System Flows and Sequence Diagrams

### Contract Creation

<img src="./diagrams/sequence_contract_creation.svg" alt="Contract Creation Sequence Diagram" style="width:100%; max-width:1400px;" />

```mermaid
sequenceDiagram
    participant User
    participant UI as Renderer
    participant API as FastAPI
    participant Service as LicenseService
    participant DB as SQLite
    User->>UI: Fill "Create Contract" form
    UI->>API: POST /api/licenses (payload)
    API->>Service: create_complete_license(data)
    Service->>DB: get_company_by_registration / add_company
    Service->>DB: get_vehicle_by_registration / add_vehicle
    Service->>DB: add_route
    Service->>DB: add_hazmat (optional)
    Service->>DB: add_license
    DB-->>Service: license_id
    Service->>DB: add_audit_log (CREATE)
    Service-->>API: license_id
    API-->>UI: 201 { status: success, data: {id} }

```

Explanation: The UI posts to the local API which delegates orchestration to `LicenseService`. The service ensures company and vehicle exist (create-if-missing), persists route/hazmat, then the license record, and finally writes an audit log. This centralization prevents inconsistent state across components.

---

### Search Workflow

<img src="./diagrams/sequence_search.svg" alt="Search Workflow Sequence Diagram" style="width:100%; max-width:1400px;" />

```mermaid
sequenceDiagram
    participant User
    participant UI as Renderer
    participant API as FastAPI
    participant DB as SQLite
    User->>UI: Enter search term / filters
    UI->>API: GET /api/licenses?search=...&page=1
    API->>DB: search_licenses(search_term, filters, pagination)
    DB-->>API: results (records + total)
    API-->>UI: {status: success, data: {records, total}}
    UI->>User: Render results
```

Explanation: Search requests are implemented by `Database.search_licenses`, which applies SQL filters and pagination. The API returns a consistent envelope (`status/message/data`) so the UI has a single parsing strategy for lists, filters, sorting, and deleted/archived views.

---

### Statistics Workflow

<img src="./diagrams/sequence_statistics.svg" alt="Statistics Workflow Sequence Diagram" style="width:100%; max-width:1400px;" />

```mermaid
sequenceDiagram
    participant UI
    participant API
    participant Stats as StatisticsService
    participant DB
    UI->>API: GET /api/statistics/dashboard
    API->>Stats: get_dashboard_statistics()
    alt cache valid
        Stats-->>API: cached payload
    else cache expired
        Stats->>DB: run aggregation queries
        DB-->>Stats: query rows
        Stats-->>API: computed payload (and cache it)
    end
    API-->>UI: {status: success, data: payload}

```

Explanation: `StatisticsService` maintains an in-memory TTL cache to avoid repeated heavy aggregation queries. When cache is valid, responses are instant; when expired, the service runs joins/aggregations, caches results, and returns structured KPI and municipality datasets used by charts.
