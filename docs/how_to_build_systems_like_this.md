# How to Build Systems Like This

## 1. The Mental Model

Building a professional desktop compliance system is not first a coding exercise. It is a translation exercise. You are translating business obligations into software structures that can be trusted, audited, and maintained years later.

The engineer’s job is to reduce ambiguity, protect data, and preserve operational confidence.

## 2. Before Coding

### 2.1 Start with the client’s real workflow

Before you write code, learn how the work is actually done:

- Who enters data?
- Who reviews it?
- Who searches it?
- Who audits it?
- What happens when a contract expires?
- What is the consequence of a mistake?

The goal is not to hear a feature list. The goal is to understand the operating environment.

### 2.2 Ask the right questions

Useful questions include:

- What is the primary record in the system?
- Which fields are mandatory for legal or operational reasons?
- Which fields are only informative?
- What should happen when a record is deleted?
- Can records be restored?
- Who needs historical traceability?
- Which actions must never silently fail?
- What is the expected data volume over time?
- Is the application single-user, shared desktop, or networked?

### 2.3 Separate facts from assumptions

Never assume a field is required just because it appears important. Confirm it.

Do not assume:

- Every company has a registration number.
- Every license has a route.
- Every user wants the same screen order.
- Every field should be normalized into its own table.

Make the domain explicit before coding.

## 3. System Thinking

### 3.1 Translate business into entities

In a hazardous material transport license system, the important entities are not UI components. They are business objects:

- Company.
- Vehicle.
- Route.
- License.
- Hazardous material.
- Audit log.
- Settings.

Each entity exists because the business needs to answer a question or preserve evidence.

### 3.2 Identify the true source of truth

Always ask which object owns the truth.

Examples:

- The license table is the canonical contract record.
- The audit log is the canonical history record.
- The settings table is the canonical runtime configuration store.

If you do not define the source of truth, duplication and contradictions appear quickly.

## 4. Architecture Design

### 4.1 Choose technologies by fit, not fashion

The stack should match the problem:

- Electron for the desktop shell.
- Python for orchestration and rules.
- FastAPI for the local API boundary.
- SQLite for local persistence.

The correct stack is the one that minimizes friction for the expected deployment model.

### 4.2 Trade-offs are not failures

Every real system has trade-offs.

Examples:

- SQLite is not ideal for multi-user network workloads, but it is excellent for local desktop persistence.
- Electron uses more memory than a native toolkit, but it drastically reduces implementation complexity.
- A local API adds process boundaries, but it keeps the frontend simple and testable.

### 4.3 Keep layers honest

Do not let the UI directly manipulate the database. Do not let the database become a place where all business logic is hidden. Each layer should have a job:

- UI: present and collect input.
- API: validate and route.
- Service: coordinate business workflows.
- Database: persist data safely.

## 5. Planning and Roadmap

### 5.1 Build in the right order

1. Understand the domain.
2. Design the data model.
3. Define API contracts.
4. Implement the backend core.
5. Build the UI around the contract.
6. Add validation and error handling.
7. Add analytics and background automation.
8. Test with real workflows.
9. Document everything.

### 5.2 Avoid premature polish

Do not spend too early on visual styling if the data model is wrong. A beautiful interface over broken data is expensive decoration.

## 6. Database Design

### 6.1 Start from cardinality

For every relationship, ask:

- Is it one-to-one?
- One-to-many?
- Many-to-many?

This determines whether a foreign key or join table is needed.

### 6.2 Design for auditability

In compliance systems, deleting data permanently is often the wrong choice.

Use:

- Soft delete for active records.
- Audit logs for history.
- Timestamps for lifecycle tracing.

### 6.3 Index for the questions users actually ask

Do not index every column. Index the columns that support:

- Searching.
- Expiry scanning.
- Filtering.
- Referential lookups.

Indexes should reflect operational reality, not theoretical completeness.

## 7. Backend Engineering

### 7.1 Keep route handlers thin

Route handlers should receive input, validate it, call services, and return responses. They should not become the place where the business process is implemented line by line.

### 7.2 Put orchestration in services

If a workflow touches multiple entities, it belongs in a service.

Examples:

- Creating a license.
- Restoring a deleted record.
- Building a dashboard payload.
- Running expiry checks.

### 7.3 Treat rules as first-class citizens

If you need to ask, “is this allowed?”, that is business logic. Do not bury it in SQL strings or UI conditionals.

## 8. Frontend and UX

### 8.1 Simplicity beats novelty

Operators need clarity more than surprise.

Good UX properties:

- Visible navigation.
- Stable layout.
- Direct feedback.
- Minimal effort to recover from mistakes.

### 8.2 Respect the operator’s time

Reduce unnecessary clicks, avoid hidden flows, and keep search and creation obvious.

### 8.3 Accessibility is operational quality

Readable contrast, clear labels, and predictable focus behavior are not optional extras. They are part of reliable software.

## 9. Error Handling

### 9.1 Anticipate failure

Do not design as if every dependency will always work.

Expect:

- Missing input.
- Locked databases.
- Invalid credentials.
- Network failure for SMTP.
- Partial data in legacy records.

### 9.2 Fail safely

When a failure happens:

- Keep the application stable.
- Return a usable message.
- Preserve evidence.
- Avoid corrupting state.

## 10. Testing

### 10.1 Test the workflow, not just the function

Professional testing verifies complete user journeys:

- Create contract.
- Search contract.
- View statistics.
- Delete and restore.
- Observe audit records.

### 10.2 Include edge cases

Test:

- Duplicate registration numbers.
- Missing required fields.
- Expired contracts.
- Empty search results.
- Backend startup failure.

## 11. Deployment

### 11.1 Local desktop delivery

The deployment story should be simple enough that another engineer can set up the app without tribal knowledge.

That means:

- Clear setup instructions.
- Repeatable dependency installation.
- A documented startup command.
- A predictable database location.

### 11.2 Runtime discipline

The application should start, verify readiness, open the UI, and close cleanly. If the startup sequence is unclear, the system is not production-grade yet.

## 12. Engineering Mindset

### 12.1 Think in causes, not symptoms

When something breaks, ask what structural choice allowed the failure.

### 12.2 Prefer explicitness

In maintainable systems, a slightly longer but explicit implementation is often better than a clever one.

### 12.3 Be careful with abstraction

Abstraction is valuable only when it removes repeated complexity. If it obscures the business process, it becomes a liability.

### 12.4 Optimize for future readers

The person reading the code next year is part of the user base.

## 13. Closing Principle

A system like this is successful when it is boring in the best possible way: predictable, auditable, recoverable, and easy to understand.
