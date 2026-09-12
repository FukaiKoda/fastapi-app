# Senior Engineer & Interviewer Persona

## Role
You are acting as a Senior Backend Engineer and a Technical Interviewer for top-tier consulting firms (like BCG) and FAANG companies. Your goal is to mentor the user, guide them through building an enterprise-grade FastAPI application, and evaluate their technical decisions as if they were in a rigorous technical interview.

## User Context
- **Background:** Student at 1337 (42 Network). Has a solid foundation in low-level programming (C/C++), memory management, networking, and building web servers/IRCs from scratch.
- **Previous Experience:** Node.js (Express, NestJS) and Java (Spring Boot). Familiar with MVC, dependency injection, and RESTful APIs.
- **Current Goal:** Learn FastAPI and the modern Python ecosystem (specifically using `uv`) from scratch. Aiming to reach enterprise-level fluency.
- **Target:** Be fully prepared for backend technical interviews and assignments (e.g., building CRUD endpoints for a JSON generator file, scaling it, and handling databases).

## Evaluation & Mentoring Criteria
When reviewing the user's code, answering questions, or guiding them to the next step, strictly enforce and evaluate the following:
1. **Clean Code & Pythonic Idioms:** Ensure the user writes code that is idiomatic to Python (PEP 8) and FastAPI, not just Java/Node translated to Python.
2. **Design Patterns & Architecture:** Evaluate the use of SOLID principles, DRY (Don't Repeat Yourself), and separation of concerns (e.g., routing vs. business logic vs. data access).
3. **System Thinking & Problem Solving:** Ask probing questions about edge cases, performance implications, memory usage (important when dealing with files/JSON), and scalability.
4. **Tooling & Ecosystem:** Encourage best practices with modern tooling like `uv`, Pydantic (v2), and proper virtual environment management.

## Workflow Rules
- **Do NOT write the code for the user.** Provide guidance, pseudocode, or snippets only when necessary.
- Ask the user to propose solutions, architectural decisions, and commands first.
- Provide thorough code reviews focusing on the evaluation criteria above.
- Maintain a professional, encouraging, but rigorous "senior engineer" tone.

---

# Project: Real-Time IoT & Analytics Dashboard API

A backend API that collects telemetry from simulated smart-home devices (temperature sensors, power meters, security cameras), processes it in real-time, stores it relationally, streams live updates via WebSockets, and triggers automated alerts on anomalous readings.

This project was chosen because it naturally exercises **every enterprise FastAPI pattern** — async I/O under high-throughput ingestion, Pydantic validation on untrusted device payloads, WebSocket broadcasting, background task processing, and non-trivial relational queries — while mapping 1:1 to concepts the user already knows from NestJS and Spring Boot.

---

## 1. Functional Requirements

### 1.1 Device Management (CRUD)
| ID | Requirement | Details |
|----|-------------|---------|
| FR-01 | **Register a device** | `POST /api/v1/devices` — Create a new IoT device record. Each device has a unique `device_id` (UUID), a `name`, a `type` (enum: `temperature_sensor`, `power_meter`, `security_camera`), a `location` (string), and a `status` (enum: `online`, `offline`, `maintenance`). |
| FR-02 | **List all devices** | `GET /api/v1/devices` — Paginated listing with filtering by `type`, `status`, and `location`. Supports `?page=1&size=20&sort_by=created_at&order=desc`. |
| FR-03 | **Get device details** | `GET /api/v1/devices/{device_id}` — Returns full device metadata plus its **latest telemetry reading** (if any). |
| FR-04 | **Update a device** | `PATCH /api/v1/devices/{device_id}` — Partial update of mutable fields (`name`, `location`, `status`). `type` and `device_id` are immutable after creation. |
| FR-05 | **Delete a device** | `DELETE /api/v1/devices/{device_id}` — Soft-delete (sets `deleted_at` timestamp). Related telemetry data is preserved for audit purposes. |

### 1.2 Telemetry Ingestion
| ID | Requirement | Details |
|----|-------------|---------|
| FR-06 | **Ingest a single telemetry reading** | `POST /api/v1/devices/{device_id}/telemetry` — Accepts a JSON payload with `timestamp` (ISO 8601), `metric_type` (enum: `temperature_celsius`, `power_watts`, `motion_detected`, `battery_percent`), and `value` (float). The endpoint must validate that the `metric_type` is compatible with the device's `type` (e.g., a `power_meter` cannot submit `temperature_celsius`). |
| FR-07 | **Batch ingest telemetry** | `POST /api/v1/telemetry/batch` — Accepts an array of up to **100 readings** in a single request (each reading includes `device_id`, `timestamp`, `metric_type`, `value`). Returns a summary: `{ "accepted": N, "rejected": M, "errors": [...] }`. This simulates high-frequency IoT data ingestion. |
| FR-08 | **Device auto-status update** | When telemetry is received for a device whose status is `offline`, the system automatically transitions the device to `online` and records the state change. |

### 1.3 Real-Time Streaming
| ID | Requirement | Details |
|----|-------------|---------|
| FR-09 | **WebSocket: Live telemetry feed** | `WS /api/v1/ws/telemetry` — Clients connect and receive a real-time stream of all incoming telemetry readings as they are ingested. Supports an optional query parameter `?device_id=<uuid>` to subscribe to a single device's feed. |
| FR-10 | **WebSocket: Device status changes** | `WS /api/v1/ws/devices/status` — Streams device status transitions (`online` → `offline`, etc.) in real-time to connected clients. |
| FR-11 | **Connection management** | The server must track active WebSocket connections, handle graceful disconnection, and broadcast only to relevant subscribers (filtered by device or topic). |

### 1.4 Alert System (Background Processing)
| ID | Requirement | Details |
|----|-------------|---------|
| FR-12 | **Define alert rules** | `POST /api/v1/alerts/rules` — Create a rule such as "If `temperature_celsius` > 80.0 for device type `temperature_sensor`, trigger alert." Each rule has: `metric_type`, `operator` (enum: `gt`, `lt`, `gte`, `lte`, `eq`), `threshold` (float), `device_type` (optional filter), and `severity` (enum: `info`, `warning`, `critical`). |
| FR-13 | **Evaluate alerts on ingestion** | Every incoming telemetry reading is evaluated against all active alert rules. If a rule matches, an **alert event** is created and persisted. This evaluation happens **asynchronously** via FastAPI `BackgroundTasks` so it does not block the ingestion response. |
| FR-14 | **List triggered alerts** | `GET /api/v1/alerts` — Paginated listing of triggered alerts with filters: `severity`, `device_id`, `acknowledged` (bool), and date range (`from_date`, `to_date`). |
| FR-15 | **Acknowledge an alert** | `PATCH /api/v1/alerts/{alert_id}/acknowledge` — Marks an alert as acknowledged by a user. Records `acknowledged_at` timestamp and `acknowledged_by` (user identifier). |

### 1.5 Historical Analytics
| ID | Requirement | Details |
|----|-------------|---------|
| FR-16 | **Device telemetry history** | `GET /api/v1/devices/{device_id}/telemetry` — Paginated historical readings with filters: `metric_type`, `from_date`, `to_date`. Sorted by timestamp descending. |
| FR-17 | **Aggregated statistics** | `GET /api/v1/analytics/summary` — Returns aggregated metrics over a configurable time window: `min`, `max`, `avg`, `count` per `device_id` and `metric_type`. Supports query params: `window` (enum: `hourly`, `daily`, `weekly`), `from_date`, `to_date`, `device_id` (optional), `metric_type` (optional). |
| FR-18 | **System dashboard stats** | `GET /api/v1/analytics/dashboard` — Returns a snapshot: total devices (by status), total telemetry readings (last 24h), active alert count (by severity), and top 5 devices by reading volume. |

### 1.6 Authentication & Authorization
| ID | Requirement | Details |
|----|-------------|---------|
| FR-19 | **User registration** | `POST /api/v1/auth/register` — Register with `email`, `password`, `full_name`. Passwords are hashed using `bcrypt`. |
| FR-20 | **User login** | `POST /api/v1/auth/login` — Returns a JWT access token (short-lived, 30 min) and a refresh token (long-lived, 7 days). Follows OAuth2 password bearer flow. |
| FR-21 | **Token refresh** | `POST /api/v1/auth/refresh` — Accepts a valid refresh token and returns a new access token. |
| FR-22 | **Protected endpoints** | All endpoints except `/auth/register`, `/auth/login`, `/auth/refresh`, and `/health` require a valid JWT in the `Authorization: Bearer <token>` header. |

### 1.7 Health & Metadata
| ID | Requirement | Details |
|----|-------------|---------|
| FR-23 | **Health check** | `GET /health` — Returns `{ "status": "healthy", "version": "0.1.0", "timestamp": "..." }`. Used by load balancers and monitoring. |
| FR-24 | **Auto-generated API docs** | FastAPI's built-in Swagger UI (`/docs`) and ReDoc (`/redoc`) must be fully functional with accurate schemas, descriptions, and example payloads for every endpoint. |

---

## 2. Non-Functional Requirements

### 2.1 Performance
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-01 | **Async-first execution** | All I/O-bound operations (database queries, WebSocket sends, background task dispatch) must use `async/await`. No synchronous blocking calls in the request path. This is FastAPI's primary advantage over Flask/Django-sync and mirrors the non-blocking I/O model you know from Node.js. |
| NFR-02 | **Ingestion throughput** | The batch ingestion endpoint (`FR-07`) must handle 100 readings per request without exceeding 200ms response time (excluding network latency) under normal database load. |
| NFR-03 | **WebSocket latency** | Telemetry readings must be broadcast to connected WebSocket clients within 100ms of ingestion (in-process, single-instance). |

### 2.2 Reliability & Error Handling
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-04 | **Structured error responses** | All errors must follow a consistent JSON schema: `{ "detail": { "code": "DEVICE_NOT_FOUND", "message": "...", "field": "..." } }`. No raw exception traces in production. This is critical for interview readiness — most candidates fail on error handling. |
| NFR-05 | **Input validation** | All request payloads are validated via Pydantic V2 models with strict typing, custom validators, and meaningful error messages. Invalid payloads return `422 Unprocessable Entity` with per-field errors. |
| NFR-06 | **Graceful degradation** | If the database is unreachable, the health endpoint must return `{ "status": "degraded" }` instead of crashing. WebSocket connections must be cleanly closed on server shutdown. |
| NFR-07 | **Idempotency** | Telemetry ingestion should be idempotent — re-submitting the same `(device_id, timestamp, metric_type)` tuple should update the existing reading, not create a duplicate. |

### 2.3 Security
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-08 | **Password hashing** | Use `bcrypt` with a work factor of 12. Never store plaintext passwords. |
| NFR-09 | **JWT best practices** | Tokens must include `exp`, `sub`, `iat` claims. Access tokens are short-lived (30 min). Refresh tokens are long-lived (7 days) and stored/tracked server-side for revocation. |
| NFR-10 | **CORS configuration** | Configurable allowed origins via environment variables. Default to restrictive policy in production. |
| NFR-11 | **Rate limiting** | Apply rate limiting to auth endpoints (e.g., 5 login attempts per minute per IP) to prevent brute-force attacks. |

### 2.4 Observability
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-12 | **Structured logging** | Use Python's `logging` module with JSON-formatted output. Every log entry must include: `timestamp`, `level`, `message`, `request_id` (correlation ID), and `module`. This mirrors the structured logging you'd see in production Spring Boot apps. |
| NFR-13 | **Request correlation** | Every incoming HTTP request is assigned a unique `X-Request-ID` (UUID). This ID is propagated through all log entries, database operations, and background tasks spawned by that request. |

### 2.5 Maintainability
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-14 | **Type safety** | 100% type-annotated codebase. Use `mypy` or `pyright` for static type checking. This is the Python equivalent of TypeScript strict mode that you're used to. |
| NFR-15 | **Test coverage** | Minimum 80% test coverage. Unit tests for services, integration tests for API endpoints using `httpx.AsyncClient` + `pytest-asyncio`. |
| NFR-16 | **Configuration management** | All environment-specific values (database URL, JWT secret, CORS origins) loaded via `pydantic-settings` from `.env` files. No hardcoded secrets. |

### 2.6 Developer Experience
| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-17 | **Hot reload** | Development server via `uvicorn` with `--reload` flag for instant feedback. |
| NFR-18 | **Database migrations** | Schema changes managed exclusively through Alembic migration scripts. No manual DDL. |
| NFR-19 | **Dependency management** | All dependencies managed via `uv` with a lockfile (`uv.lock`). Reproducible builds. |

---

## 3. Architecture Decisions

### 3.1 System Architecture: Monolith (Single Deployed Unit)

**Decision:** Deploy as a single monolithic application.

**Rationale:**
- This is a **learning project** — the goal is to master FastAPI patterns, not Kubernetes orchestration.
- A monolith eliminates operational complexity (no service mesh, no inter-service communication, no distributed tracing).
- In real interviews, you're almost always asked to build a monolith first and then discuss *how* you would decompose it into services. Knowing the monolith deeply makes that discussion credible.
- FastAPI monoliths are production-viable at surprisingly large scale (Uber's early Python services, many fintech startups) before needing decomposition.

**What this means concretely:**
- Single `uvicorn` process serving HTTP, WebSocket, and background tasks.
- Single PostgreSQL database instance.
- No message broker required (we use in-process `asyncio` patterns for pub/sub).
- The application can later be containerized in a single `Dockerfile`.

---

### 3.2 Application Architecture: Layered Architecture (N-Layer)

**Decision:** Use a **4-layer architecture** with strict dependency direction (top → bottom). This maps directly to what you know from NestJS (Controllers → Services → Repositories) and Spring Boot (Controller → Service → Repository).

**Why 4 layers instead of 3:**
In FastAPI best practices (and in production systems at companies like Netflix, Stripe, and BCG's internal platforms), there is a clear separation between **Pydantic schemas** (what the API speaks) and **SQLAlchemy models** (what the database speaks). This mapping layer is critical and deserves explicit recognition.

#### Layer 1: Presentation Layer (`api/`)
- **Responsibility:** HTTP routing, request/response handling, WebSocket endpoints, dependency injection of services.
- **Contains:** FastAPI `APIRouter` instances, path operation functions (the equivalent of NestJS `@Controller` methods or Spring `@RestController` methods).
- **Rules:**
  - No business logic here. Route handlers are thin — they validate input (via Pydantic), call a service, and return a response.
  - All Pydantic request/response schemas are defined in the `schemas/` layer, not inline.
  - Dependency injection via `Depends()` is used to inject services and database sessions.

#### Layer 2: Business Logic Layer (`services/`)
- **Responsibility:** All business rules, orchestration, validation beyond schema-level, and data transformation.
- **Contains:** Plain Python classes or functions that encapsulate domain logic.
- **Rules:**
  - Services receive and return **Pydantic schemas or domain primitives**, never raw SQLAlchemy model instances to the presentation layer.
  - Services call repositories for data access — they never construct SQL queries directly.
  - Services are where you implement: alert rule evaluation, telemetry validation (metric type vs. device type compatibility), batch processing logic, and WebSocket broadcast coordination.

#### Layer 3: Data Access Layer (`repositories/`)
- **Responsibility:** All database interactions — CRUD operations, complex queries, aggregations.
- **Contains:** Repository classes/functions that accept and return **SQLAlchemy model instances**.
- **Rules:**
  - Repositories know about SQLAlchemy models and the `AsyncSession`, nothing else.
  - No business logic in repositories. A repository does not decide *whether* to create a record — it just creates it when told to.
  - This is the equivalent of Spring Data JPA `@Repository` or TypeORM custom repositories.

#### Layer 4: Data/Model Layer (`models/` + `schemas/`)
- **Responsibility:** Define the shape of data at every boundary.
- **Contains two distinct sub-layers:**
  - **`models/`** — SQLAlchemy 2.0 ORM models (database table definitions). These are the equivalent of JPA `@Entity` classes or TypeORM entities.
  - **`schemas/`** — Pydantic V2 models (API contracts). These are the equivalent of NestJS DTOs (`CreateDeviceDto`, `DeviceResponseDto`) or Spring Boot request/response POJOs.
- **Rules:**
  - SQLAlchemy models and Pydantic schemas are **always separate**. A SQLAlchemy model is never directly returned in an API response.
  - Conversion between models and schemas happens in the **service layer**.
  - Schemas are versioned with the API (e.g., `DeviceCreateSchema`, `DeviceResponseSchema`, `DeviceUpdateSchema`).

#### Dependency Direction (Strictly Enforced)
```
Presentation (api/) → Services (services/) → Repositories (repositories/) → Models (models/)
                                                                          ↗
Schemas (schemas/) ←——— used by Presentation AND Services ———————————————
```
- **Presentation** depends on **Services** and **Schemas**.
- **Services** depend on **Repositories** and **Schemas**.
- **Repositories** depend on **Models**.
- **Models** and **Schemas** depend on nothing (they are leaf nodes).
- **NEVER** allow a lower layer to import from a higher layer.

#### Why NOT a Modular Monolith?
A modular monolith (feature-sliced: `devices/`, `telemetry/`, `alerts/`, each with their own routes/services/repos) is excellent for large teams, but for a learning project:
- It adds structural overhead that obscures the FastAPI patterns you're trying to learn.
- The layered approach makes the **separation of concerns** more visible and easier to discuss in interviews.
- Once you master layers, refactoring to modules is trivial (you just regroup by feature instead of by layer).

---

### 3.3 Data Model

**Decision:** Use **relational modeling with 3NF (Third Normal Form)** and a straightforward entity-relationship design. No DDD aggregates — that level of abstraction is unnecessary for this project's complexity and would over-engineer the learning experience.

**Rationale:**
- The domain is simple enough that DDD tactical patterns (Aggregates, Value Objects, Domain Events) add ceremony without educational value.
- 3NF eliminates data redundancy and teaches proper relational thinking — essential for SQL-heavy interview questions.
- SQLAlchemy 2.0's declarative mapping works cleanly with normalized tables.

#### Entity-Relationship Diagram
```
┌──────────────────────────────────────────────────────────────────┐
│                          users                                   │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ email           VARCHAR(255) UNIQUE NOT NULL                     │
│ hashed_password VARCHAR(255) NOT NULL                            │
│ full_name       VARCHAR(100) NOT NULL                            │
│ is_active       BOOLEAN DEFAULT TRUE                             │
│ created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│ updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                         devices                                  │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ name            VARCHAR(100) NOT NULL                            │
│ type            VARCHAR(50) NOT NULL  (enum: temperature_sensor, │
│                 power_meter, security_camera)                    │
│ location        VARCHAR(255) NOT NULL                            │
│ status          VARCHAR(20) NOT NULL DEFAULT 'offline'           │
│                 (enum: online, offline, maintenance)             │
│ created_by      UUID (FK → users.id) NOT NULL                    │
│ created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│ updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│ deleted_at      TIMESTAMPTZ NULLABLE  (soft delete)              │
│──────────────────────────────────────────────────────────────────│
│ INDEX: idx_devices_type ON (type)                                │
│ INDEX: idx_devices_status ON (status)                            │
│ INDEX: idx_devices_deleted_at ON (deleted_at)                    │
└──────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     telemetry_readings                           │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ device_id       UUID (FK → devices.id) NOT NULL                  │
│ timestamp       TIMESTAMPTZ NOT NULL                             │
│ metric_type     VARCHAR(50) NOT NULL  (enum: temperature_celsius,│
│                 power_watts, motion_detected, battery_percent)   │
│ value           DOUBLE PRECISION NOT NULL                        │
│ created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│──────────────────────────────────────────────────────────────────│
│ UNIQUE: uq_telemetry_device_ts_metric                           │
│         ON (device_id, timestamp, metric_type)  ← idempotency   │
│ INDEX:  idx_telemetry_device_id ON (device_id)                   │
│ INDEX:  idx_telemetry_timestamp ON (timestamp)                   │
│ INDEX:  idx_telemetry_device_ts ON (device_id, timestamp DESC)   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       alert_rules                                │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ name            VARCHAR(100) NOT NULL                             │
│ metric_type     VARCHAR(50) NOT NULL                             │
│ operator        VARCHAR(10) NOT NULL  (enum: gt, lt, gte, lte,   │
│                 eq)                                               │
│ threshold       DOUBLE PRECISION NOT NULL                        │
│ device_type     VARCHAR(50) NULLABLE  (filter scope)             │
│ severity        VARCHAR(20) NOT NULL  (enum: info, warning,      │
│                 critical)                                         │
│ is_active       BOOLEAN DEFAULT TRUE                             │
│ created_by      UUID (FK → users.id) NOT NULL                    │
│ created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│ updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      alert_events                                │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ rule_id         UUID (FK → alert_rules.id) NOT NULL              │
│ device_id       UUID (FK → devices.id) NOT NULL                  │
│ reading_id      UUID (FK → telemetry_readings.id) NOT NULL       │
│ severity        VARCHAR(20) NOT NULL                             │
│ message         TEXT NOT NULL                                    │
│ acknowledged    BOOLEAN DEFAULT FALSE                            │
│ acknowledged_by UUID (FK → users.id) NULLABLE                    │
│ acknowledged_at TIMESTAMPTZ NULLABLE                             │
│ triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│──────────────────────────────────────────────────────────────────│
│ INDEX: idx_alerts_severity ON (severity)                         │
│ INDEX: idx_alerts_device_id ON (device_id)                       │
│ INDEX: idx_alerts_acknowledged ON (acknowledged)                 │
│ INDEX: idx_alerts_triggered_at ON (triggered_at DESC)            │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     refresh_tokens                               │
│──────────────────────────────────────────────────────────────────│
│ id              UUID (PK)                                        │
│ user_id         UUID (FK → users.id) NOT NULL                    │
│ token_hash      VARCHAR(255) NOT NULL UNIQUE                     │
│ expires_at      TIMESTAMPTZ NOT NULL                             │
│ revoked         BOOLEAN DEFAULT FALSE                            │
│ created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()               │
│──────────────────────────────────────────────────────────────────│
│ INDEX: idx_refresh_tokens_user_id ON (user_id)                   │
│ INDEX: idx_refresh_tokens_expires ON (expires_at)                │
└──────────────────────────────────────────────────────────────────┘
```

#### Key Design Decisions
1. **UUIDs as primary keys** — Prevents sequential ID enumeration attacks. Standard practice at FAANG and fintech companies. Slight performance trade-off vs. auto-increment integers, but negligible at our scale.
2. **Soft deletes on devices** — `deleted_at` column instead of physical deletion. Preserves telemetry data integrity and audit trail.
3. **Idempotency via unique constraint** — The `(device_id, timestamp, metric_type)` unique constraint on `telemetry_readings` ensures that re-submitting the same reading results in an upsert, not a duplicate.
4. **Denormalized `severity` on `alert_events`** — Copied from `alert_rules` at trigger time so that historical alerts remain accurate even if the rule's severity is later changed.
5. **Refresh token hashing** — Only the hash is stored, never the raw token. Same security principle as password hashing.

---

### 3.4 Communication Types

| Protocol | Usage | Endpoints | Rationale |
|----------|-------|-----------|-----------|
| **REST (HTTP/JSON)** | Primary API communication | All CRUD endpoints, analytics queries, auth flows | Industry standard. Request-response pattern. Stateless. Cached via HTTP headers. |
| **WebSocket** | Real-time streaming | `WS /api/v1/ws/telemetry`, `WS /api/v1/ws/devices/status` | Server-push pattern for live data. Lower overhead than polling. You need to learn this for any real-time system interview. |
| **In-process async pub/sub** | Internal event broadcasting | Telemetry ingestion → WebSocket broadcast, Telemetry ingestion → Alert evaluation | Uses Python `asyncio` primitives (`asyncio.Queue`, or a simple in-memory pub/sub bus). No external broker needed for single-instance deployment. |

#### What We Explicitly Avoid (and Why)
- **gRPC** — Overkill for a monolith. Useful in microservices, but not our architecture.
- **Server-Sent Events (SSE)** — WebSockets are more flexible (bidirectional) and teach you more. SSE is a subset of what WebSockets can do.
- **Message Queues (RabbitMQ/Kafka)** — No distributed components to coordinate. In-process `BackgroundTasks` and `asyncio` are sufficient. We can discuss *when* you'd introduce a broker in interview scenarios.

---

## 4. Folder Architecture

```
fastapi-app/
├── pyproject.toml                    # Project metadata & dependencies (managed by uv)
├── uv.lock                          # Locked dependency versions
├── .python-version                  # Python version pin
├── .env                             # Local environment variables (git-ignored)
├── .env.example                     # Template for required env vars (committed)
├── alembic.ini                      # Alembic configuration
├── AGENTS.md                        # This file — project spec & mentoring context
├── README.md                        # Project overview & setup instructions
│
├── alembic/                         # Database migration scripts
│   ├── env.py                       # Alembic environment (async engine setup)
│   ├── script.py.mako               # Migration template
│   └── versions/                    # Auto-generated migration files
│       └── 001_initial_schema.py
│
├── src/
│   └── fastapi_app/
│       ├── __init__.py              # Package init
│       ├── main.py                  # Application entry point: creates FastAPI app,
│       │                            # includes routers, registers startup/shutdown
│       │                            # events, configures CORS & exception handlers
│       │
│       ├── core/                    # Cross-cutting concerns (shared across all layers)
│       │   ├── __init__.py
│       │   ├── config.py            # pydantic-settings: Settings class loading from .env
│       │   ├── database.py          # Async SQLAlchemy engine, sessionmaker, get_db dependency
│       │   ├── security.py          # JWT creation/verification, password hashing utilities
│       │   ├── exceptions.py        # Custom exception classes (DeviceNotFoundError, etc.)
│       │   ├── exception_handlers.py # FastAPI exception handler registrations
│       │   ├── logging.py           # Structured logging setup (JSON formatter, correlation ID)
│       │   ├── dependencies.py      # Shared FastAPI dependencies (get_current_user, pagination)
│       │   └── events.py            # In-memory async event bus (pub/sub for WebSocket broadcast)
│       │
│       ├── models/                  # SQLAlchemy 2.0 ORM models (Layer 4 — database shape)
│       │   ├── __init__.py          # Re-exports all models for Alembic auto-detection
│       │   ├── base.py              # Declarative base class with common columns
│       │   │                        # (id, created_at, updated_at)
│       │   ├── user.py              # User model
│       │   ├── device.py            # Device model
│       │   ├── telemetry.py         # TelemetryReading model
│       │   ├── alert_rule.py        # AlertRule model
│       │   ├── alert_event.py       # AlertEvent model
│       │   └── refresh_token.py     # RefreshToken model
│       │
│       ├── schemas/                 # Pydantic V2 schemas (Layer 4 — API contracts)
│       │   ├── __init__.py
│       │   ├── common.py            # Shared schemas: PaginationParams, PaginatedResponse,
│       │   │                        # ErrorResponse, HealthResponse
│       │   ├── auth.py              # UserRegisterSchema, UserLoginSchema, TokenResponse,
│       │   │                        # RefreshTokenRequest
│       │   ├── device.py            # DeviceCreateSchema, DeviceUpdateSchema,
│       │   │                        # DeviceResponseSchema, DeviceListResponse
│       │   ├── telemetry.py         # TelemetryCreateSchema, TelemetryBatchSchema,
│       │   │                        # TelemetryResponseSchema, BatchResultSchema
│       │   ├── alert.py             # AlertRuleCreateSchema, AlertRuleResponseSchema,
│       │   │                        # AlertEventResponseSchema, AlertAcknowledgeSchema
│       │   └── analytics.py         # AggregatedMetricSchema, DashboardStatsSchema
│       │
│       ├── repositories/            # Data access layer (Layer 3 — database queries)
│       │   ├── __init__.py
│       │   ├── base.py              # Generic async CRUD base repository
│       │   ├── user_repository.py   # User-specific queries (find_by_email, etc.)
│       │   ├── device_repository.py # Device CRUD + filtered listing
│       │   ├── telemetry_repository.py  # Telemetry insert, batch insert, history queries
│       │   ├── alert_rule_repository.py # Alert rule CRUD
│       │   ├── alert_event_repository.py # Alert event queries, acknowledgment
│       │   └── analytics_repository.py  # Aggregation queries (GROUP BY, window functions)
│       │
│       ├── services/                # Business logic layer (Layer 2)
│       │   ├── __init__.py
│       │   ├── auth_service.py      # Registration, login, token refresh, password verification
│       │   ├── device_service.py    # Device lifecycle management, status transitions
│       │   ├── telemetry_service.py # Ingestion logic, metric/device type validation,
│       │   │                        # event bus publishing, batch processing
│       │   ├── alert_service.py     # Rule evaluation engine, alert creation, acknowledgment
│       │   ├── analytics_service.py # Aggregation orchestration, dashboard stats assembly
│       │   └── websocket_service.py # Connection manager, subscription handling, broadcast
│       │
│       └── api/                     # Presentation layer (Layer 1 — HTTP/WS routing)
│           ├── __init__.py
│           ├── v1/                   # API version namespace
│           │   ├── __init__.py
│           │   ├── router.py        # Aggregates all v1 routers into a single APIRouter
│           │   ├── auth.py          # POST /register, POST /login, POST /refresh
│           │   ├── devices.py       # CRUD routes for devices
│           │   ├── telemetry.py     # Single + batch ingestion routes
│           │   ├── alerts.py        # Alert rule CRUD + alert listing + acknowledge
│           │   ├── analytics.py     # Summary + dashboard stats routes
│           │   └── websockets.py    # WebSocket endpoint handlers
│           └── health.py            # GET /health (unversioned)
│
└── tests/                           # Test suite (mirrors src structure)
    ├── __init__.py
    ├── conftest.py                  # Shared fixtures: async test client, test database,
    │                                # factory functions for test data
    ├── unit/                        # Unit tests (services + repositories, mocked deps)
    │   ├── __init__.py
    │   ├── test_device_service.py
    │   ├── test_telemetry_service.py
    │   ├── test_alert_service.py
    │   └── test_auth_service.py
    │
    └── integration/                 # Integration tests (full HTTP request cycle)
        ├── __init__.py
        ├── test_device_endpoints.py
        ├── test_telemetry_endpoints.py
        ├── test_alert_endpoints.py
        ├── test_auth_endpoints.py
        └── test_websocket_endpoints.py
```

#### Architecture Notes

1. **`core/` is NOT a layer** — It's a shared utility package that any layer can import. It contains cross-cutting concerns (config, DB session, security, logging) that don't belong to any single layer. This is equivalent to NestJS's `@nestjs/common` or Spring's `@Configuration` classes.

2. **`api/v1/`** — The `v1/` namespace allows future API versioning (`v2/`) without breaking existing clients. This is standard practice at Google, Stripe, and most enterprise APIs.

3. **`models/base.py`** — A `Base` declarative class with common columns (`id` as UUID, `created_at`, `updated_at`) that all models inherit from. Eliminates repetition (DRY). Equivalent to a JPA `@MappedSuperclass`.

4. **`repositories/base.py`** — A generic async CRUD repository that provides `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()` for any SQLAlchemy model. Specific repositories extend it with custom queries. This is the **Repository Pattern** — identical in concept to Spring Data JPA's `JpaRepository<T, ID>`.

5. **Tests mirror source** — `tests/unit/` tests services with mocked repositories. `tests/integration/` tests the full HTTP stack using `httpx.AsyncClient` against a test database. This separation is critical for fast CI feedback.

---

## 5. Technology Stack

### 5.1 Core Framework & Runtime

| Tool | Version | Purpose | Why This Choice |
|------|---------|---------|-----------------|
| **Python** | 3.14+ | Runtime | Latest stable. Required by project's `pyproject.toml`. |
| **FastAPI** | 0.141+ | Web framework | Async-first, Pydantic-native, auto-generated OpenAPI docs. The framework we're learning. |
| **Uvicorn** | latest | ASGI server | The reference ASGI server for FastAPI. Supports HTTP/1.1, HTTP/2, and WebSockets. Ships with `fastapi[standard]`. |
| **uv** | latest | Package & project manager | Modern, fast Python package manager. Replaces pip, pip-tools, virtualenv, and pyenv in a single tool. This is what the user is learning alongside FastAPI. |

### 5.2 Data Validation & Serialization

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **Pydantic V2** | Request/response validation, settings management | Ships with FastAPI. Rust-powered validation core (pydantic-core). Equivalent to `class-validator` in NestJS or Jakarta Bean Validation in Spring. |
| **pydantic-settings** | Environment configuration | Loads `.env` files into typed Python dataclasses. Replaces `python-dotenv` + manual parsing. Production standard. |

### 5.3 Database & ORM

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **PostgreSQL** | Relational database | Industry standard for production APIs. Rich feature set (JSONB, window functions, full-text search). Used universally at FAANG and consulting firms. |
| **SQLAlchemy 2.0** | ORM & query builder | The mature, battle-tested Python ORM. 2.0 style uses modern Python type annotations and supports async natively via `AsyncSession`. We use SQLAlchemy directly (not SQLModel) because it's what you'll encounter in enterprise codebases. |
| **asyncpg** | Async PostgreSQL driver | The fastest async PostgreSQL driver for Python. Used as the backend for `sqlalchemy[asyncio]`. |
| **Alembic** | Database migrations | The standard migration tool for SQLAlchemy. Equivalent to TypeORM migrations or Flyway in Spring Boot. Supports auto-generation of migration scripts from model changes. |

### 5.4 Authentication & Security

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **python-jose[cryptography]** | JWT token creation & verification | Standard library for JWT handling in Python. The `cryptography` extra provides robust algorithm support (RS256, HS256). |
| **passlib[bcrypt]** | Password hashing | Battle-tested password hashing library. `bcrypt` scheme with configurable work factor. |

### 5.5 Testing

| Library | Purpose | Why This Choice |
|---------|---------|-----------------|
| **pytest** | Test framework | The Python testing standard. Fixture-based, plugin-rich. |
| **pytest-asyncio** | Async test support | Enables `async def test_` functions. Required for testing async FastAPI services and repositories. |
| **httpx** | Async HTTP test client | FastAPI's recommended test client. Used via `httpx.AsyncClient` with `ASGITransport` for in-process integration testing (no real server needed). |
| **pytest-cov** | Coverage reporting | Generates coverage reports to enforce NFR-15 (80% minimum). |

### 5.6 Development & Code Quality

| Tool | Purpose | Why This Choice |
|------|---------|-----------------|
| **ruff** | Linter & formatter | Replaces `flake8`, `isort`, `black`, and `pyflakes` in a single Rust-powered tool. Extremely fast. Becoming the industry standard. |
| **mypy** or **pyright** | Static type checker | Enforces type safety (NFR-14). Catches bugs before runtime. |
| **pre-commit** | Git hooks | Runs ruff + type checking on every commit. Prevents bad code from entering the repo. |

### 5.7 Observability (Built-in, no external dependencies for Phase 1)

| Tool | Purpose | Why This Choice |
|------|---------|-----------------|
| **Python `logging`** | Structured logging | Standard library. Configured with a JSON formatter for structured output. No need for third-party logging libraries initially. |
| **Custom middleware** | Request correlation ID | A lightweight FastAPI middleware that generates/propagates `X-Request-ID` headers. |

### 5.8 Libraries NOT Included (and Why)

| Library | Why Excluded |
|---------|-------------|
| **SQLModel** | Merges Pydantic and SQLAlchemy into one class. While convenient, it hides the boundary between API schema and database model — a boundary you must understand deeply for interviews. It's also less mature and has fewer production deployments. |
| **Celery / ARQ** | External task queue. Requires a broker (Redis/RabbitMQ), worker processes, and operational overhead. FastAPI's `BackgroundTasks` + `asyncio` are sufficient for our single-instance monolith. We'll discuss when Celery becomes necessary as a system design talking point. |
| **Redis** | Not needed for Phase 1. In-memory pub/sub via `asyncio` handles WebSocket broadcasting. Redis becomes relevant when scaling to multiple server instances (Phase 4, if we get there). |
| **Docker / Docker Compose** | Not part of the FastAPI learning path. We develop locally with `uv` and `uvicorn`. Containerization is a deployment concern, not an application concern. Can be added as a final polish step. |

---

## 6. Implementation Phases

### Phase 1: Foundation & Device CRUD
- Project structure setup per Section 4.
- `core/config.py` with `pydantic-settings`.
- PostgreSQL + SQLAlchemy async setup (`core/database.py`).
- Alembic initialization and first migration.
- `Device` model + CRUD endpoints (FR-01 through FR-05).
- Health check endpoint (FR-23).
- Structured error handling (NFR-04).
- Structured logging (NFR-12).

### Phase 2: Telemetry Ingestion & Validation
- `TelemetryReading` model + migration.
- Single and batch ingestion endpoints (FR-06, FR-07).
- Metric-type/device-type compatibility validation.
- Idempotency via upsert (NFR-07).
- Auto-status update (FR-08).

### Phase 3: Authentication & Authorization
- `User` + `RefreshToken` models + migrations.
- Auth endpoints: register, login, refresh (FR-19 through FR-21).
- JWT middleware and `get_current_user` dependency (FR-22).
- Protect all existing endpoints.

### Phase 4: Real-Time WebSocket Layer
- In-memory event bus (`core/events.py`).
- WebSocket connection manager (`services/websocket_service.py`).
- Live telemetry feed (FR-09).
- Device status stream (FR-10).
- Graceful connection handling (FR-11).

### Phase 5: Alert System
- `AlertRule` + `AlertEvent` models + migrations.
- Alert rule CRUD (FR-12).
- Background alert evaluation on ingestion (FR-13).
- Alert listing and acknowledgment (FR-14, FR-15).

### Phase 6: Analytics & Polish
- Aggregation queries (FR-17).
- Dashboard stats endpoint (FR-18).
- Telemetry history with pagination (FR-16).
- Rate limiting (NFR-11).
- Full test suite (NFR-15).
- API documentation polish (FR-24).

---

## 7. Concept Mapping: NestJS / Spring Boot → FastAPI

This reference table helps translate your existing knowledge to FastAPI patterns.

| Concept | NestJS | Spring Boot | FastAPI |
|---------|--------|-------------|---------|
| Entry point | `main.ts` / `AppModule` | `@SpringBootApplication` | `main.py` / `FastAPI()` |
| Route definition | `@Controller` + `@Get/@Post` | `@RestController` + `@GetMapping` | `APIRouter` + `@router.get/@router.post` |
| Request validation | `class-validator` DTO | `@Valid` + Jakarta annotations | Pydantic model as parameter type |
| Response serialization | `class-transformer` | Jackson `@JsonProperty` | Pydantic `model_dump()` + `response_model` |
| Dependency injection | `@Injectable()` + constructor | `@Component` + `@Autowired` | `Depends()` function parameter |
| Database session | TypeORM `DataSource` | Spring `EntityManager` | `AsyncSession` via `Depends(get_db)` |
| ORM entity | `@Entity` TypeORM decorator | `@Entity` JPA annotation | SQLAlchemy `DeclarativeBase` subclass |
| Repository pattern | TypeORM `Repository<T>` | `JpaRepository<T, ID>` | Custom class with `AsyncSession` |
| Middleware | `@Middleware` | `HandlerInterceptor` / Filter | `@app.middleware("http")` or Starlette `BaseHTTPMiddleware` |
| Guards / Auth | `@UseGuards(AuthGuard)` | `@PreAuthorize` / Spring Security | `Depends(get_current_user)` |
| Exception handling | `@Catch` + Exception Filter | `@ControllerAdvice` | `@app.exception_handler(ExcClass)` |
| Config management | `@nestjs/config` + `.env` | `application.yml` / `@Value` | `pydantic-settings` + `.env` |
| Background tasks | Bull queue / `@nestjs/schedule` | `@Async` / Spring Batch | `BackgroundTasks` / `asyncio.create_task` |
| WebSocket | `@WebSocketGateway` | Spring WebSocket / STOMP | `@app.websocket("/path")` |
| Testing | Jest + `@nestjs/testing` | JUnit + MockMvc | pytest + `httpx.AsyncClient` |
| Migrations | TypeORM CLI migrations | Flyway / Liquibase | Alembic |
| API versioning | Module imports + prefix | `@RequestMapping("/v1")` | `APIRouter(prefix="/api/v1")` |
