# Roadmap: Real-Time IoT & Analytics Dashboard API

> **How to use this roadmap:** Work through tasks **sequentially**. Each task has a clear deliverable
> and a set of concepts you'll learn. Propose your solution first, then ask for review.
> Tasks marked with 🧠 have an **interview question** embedded — I'll ask you to explain your
> reasoning as if you were in a technical interview.

> **Legend:**
> - `[ ]` — Not started
> - `[/]` — In progress
> - `[x]` — Completed

---

## Phase 1: Foundation & Device CRUD

**Goal:** Stand up the full project skeleton, connect to PostgreSQL asynchronously, and implement your first
complete CRUD domain (Devices) with proper layered architecture, error handling, and logging.

**What you'll learn:** FastAPI app lifecycle, `uv` workflows, Pydantic V2 settings, SQLAlchemy 2.0 async,
Alembic migrations, the Repository Pattern in Python, structured error handling, and dependency injection
via `Depends()`.

---

### Task 1.1 — Project Scaffolding & Dev Tooling

**Deliverable:** The full folder structure from [AGENTS.md Section 4](file:///home/iheemz/fastapi-app/AGENTS.md) exists with empty `__init__.py`
files in every package. `ruff` is configured. The dev server starts and returns `{"detail": "Not Found"}` on any route.

- [ ] **1.1.1** — Create the complete directory tree under `src/fastapi_app/` per the folder architecture:
  `core/`, `models/`, `schemas/`, `repositories/`, `services/`, `api/`, `api/v1/`.
  Create empty `__init__.py` in every package directory.
  - 📂 Files to create: ~15 `__init__.py` files + empty directories
  - 🔑 Concept: Python package structure, `src` layout vs flat layout

- [ ] **1.1.2** — Create `src/fastapi_app/main.py` with a minimal FastAPI app instance.
  - The app should have a `title`, `description`, and `version` set.
  - The app should have `lifespan` context manager (even if empty for now — it's the modern replacement for `on_event`).
  - Run it with `uv run uvicorn fastapi_app.main:app --reload` and confirm `/docs` loads.
  - 🔑 Concept: FastAPI app initialization, ASGI lifespan protocol
  - 🧠 *Interview Q: What is the difference between `@app.on_event("startup")` and the `lifespan` context manager? Why did FastAPI deprecate the former?*

- [ ] **1.1.3** — Add `ruff` as a dev dependency and configure it in `pyproject.toml`.
  - Add a `[tool.ruff]` section with `line-length = 99`, `target-version = "py314"`.
  - Enable rule sets: `["E", "F", "I", "N", "UP", "B", "SIM", "RUF"]`.
  - Run `uv run ruff check .` and `uv run ruff format .` to confirm it works.
  - 🔑 Concept: Python linting ecosystem, why `ruff` replaced `black` + `flake8` + `isort`

- [ ] **1.1.4** — Create `.env.example` with placeholder values for all config we'll need:
  ```
  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/iot_dashboard
  JWT_SECRET_KEY=change-me-in-production
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  REFRESH_TOKEN_EXPIRE_DAYS=7
  CORS_ALLOWED_ORIGINS=["http://localhost:3000"]
  LOG_LEVEL=DEBUG
  ```
  Copy it to `.env` (which should be in `.gitignore`).
  - 🔑 Concept: 12-factor app configuration, secret management

---

### Task 1.2 — Configuration with `pydantic-settings`

**Deliverable:** `core/config.py` contains a `Settings` class that loads all config from `.env`. A `get_settings()`
dependency is available for injection. NFR-16 is satisfied.

- [ ] **1.2.1** — Install `pydantic-settings`: `uv add pydantic-settings`
  - 🔑 Concept: `uv add` vs `pip install`, how `uv.lock` ensures reproducibility

- [ ] **1.2.2** — Implement `core/config.py`:
  - Create a `Settings` class inheriting from `BaseSettings`.
  - Define typed fields for every value in `.env.example`.
  - Use `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`.
  - Use `@lru_cache` on a `get_settings()` function so settings are loaded once (singleton pattern).
  - 🔑 Concept: Pydantic V2 `BaseSettings`, `SettingsConfigDict`, `@lru_cache` for singletons
  - 🧠 *Interview Q: Why use `@lru_cache` on `get_settings()` instead of a module-level global? What happens if you use `Depends(get_settings)` without caching?*

- [ ] **1.2.3** — Write a quick smoke test: import `get_settings()` in `main.py`, print `settings.DATABASE_URL`
  on startup (inside the lifespan), confirm it loads from `.env`.

---

### Task 1.3 — Structured Logging Setup

**Deliverable:** `core/logging.py` configures Python's `logging` module with JSON output. Every log line includes
`timestamp`, `level`, `message`, and `module`. NFR-12 partially satisfied (correlation ID comes later).

- [ ] **1.3.1** — Implement `core/logging.py`:
  - Create a custom `logging.Formatter` subclass that outputs JSON.
  - Create a `setup_logging(log_level: str)` function that configures the root logger.
  - Call `setup_logging()` inside the `lifespan` context manager in `main.py`.
  - 🔑 Concept: Python `logging` module internals, custom formatters, structured logging
  - 🧠 *Interview Q: Why JSON-formatted logs instead of plain text? How does this affect log aggregation in production (ELK, CloudWatch, Datadog)?*

- [ ] **1.3.2** — Add a test log in `main.py` lifespan: `logger.info("Application starting", extra={"version": settings.VERSION})`.
  Confirm the output is valid JSON in the terminal.

---

### Task 1.4 — Database Connection (SQLAlchemy 2.0 Async)

**Deliverable:** `core/database.py` creates an async SQLAlchemy engine and session factory. A `get_db()` async
generator dependency yields `AsyncSession` instances. PostgreSQL is reachable.

- [ ] **1.4.1** — Install database dependencies: `uv add "sqlalchemy[asyncio]" asyncpg alembic`
  - 🔑 Concept: SQLAlchemy extras (`[asyncio]`), why `asyncpg` vs `psycopg`

- [ ] **1.4.2** — Set up a local PostgreSQL database:
  - Create a database named `iot_dashboard`.
  - Confirm you can connect via `psql` or a client.
  - Update your `.env` with the correct `DATABASE_URL`.

- [ ] **1.4.3** — Implement `core/database.py`:
  - Create `async_engine` using `create_async_engine(settings.DATABASE_URL, echo=True)`.
  - Create `async_session_factory` using `async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)`.
  - Implement `async def get_db() -> AsyncGenerator[AsyncSession, None]` as an async generator that yields a session and handles cleanup.
  - 🔑 Concept: Async context managers, `AsyncSession` lifecycle, `expire_on_commit=False` and why it matters
  - 🧠 *Interview Q: What does `expire_on_commit=False` do? When would you want it to be `True`? What happens if you access a relationship attribute after the session is closed?*

- [ ] **1.4.4** — Test the connection: Inside the `lifespan`, execute a raw `SELECT 1` using the engine to verify
  the database is reachable. Log success/failure.

---

### Task 1.5 — Base Model & Alembic Setup

**Deliverable:** `models/base.py` defines a `Base` declarative class with shared columns (`id`, `created_at`,
`updated_at`). Alembic is initialized and can generate migrations against the database.

- [ ] **1.5.1** — Implement `models/base.py`:
  - Create a `Base` class using `DeclarativeBase` (SQLAlchemy 2.0 style).
  - Add a mixin or base columns: `id` (UUID, primary key, server-default `gen_random_uuid()`), `created_at` (TIMESTAMPTZ, server-default `now()`), `updated_at` (TIMESTAMPTZ, server-default `now()`, `onupdate`).
  - 🔑 Concept: `DeclarativeBase` vs `declarative_base()`, `Mapped[]` type annotations, server-side defaults
  - 🧠 *Interview Q: Why use `server_default` (database-side) instead of `default` (Python-side) for `created_at`? What's the difference in behavior?*

- [ ] **1.5.2** — Initialize Alembic: `uv run alembic init alembic`
  - Edit `alembic.ini`: set `sqlalchemy.url` to empty (we'll load from env).
  - Edit `alembic/env.py`:
    - Import your `Base.metadata` and `Settings`.
    - Override `sqlalchemy.url` from `settings.DATABASE_URL`.
    - Configure for async migrations using `run_async_migrations()`.
  - 🔑 Concept: Alembic async configuration, `target_metadata`, migration environments
  - 🧠 *Interview Q: Why manage migrations with Alembic instead of `Base.metadata.create_all()`? What problems does `create_all()` cause in production?*

- [ ] **1.5.3** — Generate an empty migration to verify the pipeline:
  `uv run alembic revision --autogenerate -m "initial empty"`.
  Apply it: `uv run alembic upgrade head`. Confirm no errors.

---

### Task 1.6 — Device Model & First Migration

**Deliverable:** `models/device.py` defines the `Device` SQLAlchemy model matching the ER diagram. A migration
creates the `devices` table in PostgreSQL with all columns and indexes.

- [ ] **1.6.1** — Implement `models/device.py`:
  - Inherit from `Base`.
  - Define all columns per the ER diagram: `id`, `name`, `type`, `location`, `status`, `created_by`, `created_at`, `updated_at`, `deleted_at`.
  - Use Python `enum.Enum` for `DeviceType` and `DeviceStatus`. Map them to `VARCHAR` in the database.
  - Add indexes: `idx_devices_type`, `idx_devices_status`, `idx_devices_deleted_at`.
  - 🔑 Concept: SQLAlchemy `Mapped[]` annotations, `mapped_column()`, `Index()`, Python enums with SQLAlchemy
  - 🧠 *Interview Q: Should you use PostgreSQL `ENUM` type or `VARCHAR` with a check constraint for the `type` column? What are the trade-offs of each approach for schema evolution?*

- [ ] **1.6.2** — Import the `Device` model in `models/__init__.py` so Alembic can detect it.

- [ ] **1.6.3** — Generate the migration: `uv run alembic revision --autogenerate -m "add devices table"`.
  - **Review the generated migration file** before applying. Check that all columns, types, indexes, and defaults are correct.
  - Apply: `uv run alembic upgrade head`.
  - Verify: Connect to PostgreSQL and run `\d devices` to inspect the table.

---

### Task 1.7 — Device Pydantic Schemas

**Deliverable:** `schemas/device.py` contains `DeviceCreateSchema`, `DeviceUpdateSchema`, `DeviceResponseSchema`,
and `DeviceListResponse`. All schemas have proper validation, examples, and documentation strings.

- [ ] **1.7.1** — Implement shared schemas in `schemas/common.py`:
  - `PaginationParams` — A Pydantic model (or dataclass) for `page`, `size`, `sort_by`, `order` query parameters with defaults and validation.
  - `PaginatedResponse[T]` — A generic paginated response wrapper: `{ "items": [...], "total": N, "page": N, "size": N, "pages": N }`.
  - `ErrorResponse` — Structured error schema matching NFR-04: `{ "detail": { "code": "...", "message": "...", "field": "..." } }`.
  - 🔑 Concept: Pydantic generics, `model_config`, `json_schema_extra` for OpenAPI examples

- [ ] **1.7.2** — Implement `schemas/device.py`:
  - `DeviceCreateSchema` — Fields: `name`, `type` (enum), `location`. Validate `name` length (3–100 chars).
  - `DeviceUpdateSchema` — All fields optional (partial update). `type` is NOT included (immutable). Use `model_validator` to ensure at least one field is provided.
  - `DeviceResponseSchema` — Full device representation for API responses. Includes `id`, `name`, `type`, `location`, `status`, `created_at`, `updated_at`. Uses `model_config = ConfigDict(from_attributes=True)` for ORM compatibility.
  - `DeviceListResponse` — Alias for `PaginatedResponse[DeviceResponseSchema]`.
  - 🔑 Concept: Pydantic V2 `ConfigDict`, `from_attributes`, `model_validator`, enum serialization
  - 🧠 *Interview Q: Why separate `Create`, `Update`, and `Response` schemas instead of one unified `Device` schema? How does this relate to the Interface Segregation Principle?*

---

### Task 1.8 — Custom Exceptions & Error Handlers

**Deliverable:** `core/exceptions.py` defines custom exception classes. `core/exception_handlers.py` registers
FastAPI handlers that convert exceptions to structured JSON responses (NFR-04).

- [ ] **1.8.1** — Implement `core/exceptions.py`:
  - Create a base `AppException(Exception)` with `code: str`, `message: str`, `status_code: int`.
  - Create specific exceptions: `DeviceNotFoundError`, `DeviceAlreadyDeletedError`, `ValidationError`.
  - 🔑 Concept: Custom exception hierarchies in Python, `__init__` patterns

- [ ] **1.8.2** — Implement `core/exception_handlers.py`:
  - Register a handler for `AppException` that returns `JSONResponse` with the structured error schema.
  - Override FastAPI's default `RequestValidationError` handler to match your error schema format.
  - Override the `HTTPException` handler for consistency.
  - Register all handlers in `main.py`.
  - 🔑 Concept: `@app.exception_handler()`, how FastAPI/Starlette exception propagation works
  - 🧠 *Interview Q: What happens if you raise a Python `ValueError` inside a route handler without a registered exception handler? How does FastAPI handle unhandled exceptions by default? Why is this a security concern?*

---

### Task 1.9 — Device Repository (Data Access Layer)

**Deliverable:** `repositories/base.py` provides generic async CRUD. `repositories/device_repository.py`
extends it with device-specific queries (filtered listing, soft-delete).

- [ ] **1.9.1** — Implement `repositories/base.py`:
  - Create a generic `BaseRepository[T]` class (where `T` is a SQLAlchemy model type).
  - Methods: `async create(obj)`, `async get_by_id(id)`, `async get_all(skip, limit)`, `async update(id, data)`, `async delete(id)`.
  - The class receives `AsyncSession` via its constructor.
  - 🔑 Concept: Python generics with `TypeVar`, Generic classes, async context management
  - 🧠 *Interview Q: In Spring Boot, `JpaRepository<T, ID>` uses Java generics. How does Python's `TypeVar` + `Generic[T]` compare? What are the limitations of Python generics vs Java's?*

- [ ] **1.9.2** — Implement `repositories/device_repository.py`:
  - Extend `BaseRepository[Device]`.
  - Add: `async get_all_filtered(type, status, location, page, size, sort_by, order)` — builds a dynamic query with optional filters.
  - Add: `async soft_delete(device_id)` — sets `deleted_at` instead of deleting.
  - All queries must filter out soft-deleted records by default (`WHERE deleted_at IS NULL`).
  - 🔑 Concept: Dynamic query building with SQLAlchemy `select()`, `where()`, `order_by()`, `offset()`, `limit()`

---

### Task 1.10 — Device Service (Business Logic Layer)

**Deliverable:** `services/device_service.py` implements all device business logic, orchestrates repository
calls, and converts between SQLAlchemy models and Pydantic schemas.

- [ ] **1.10.1** — Implement `services/device_service.py`:
  - Methods: `create_device(schema, created_by)`, `get_device(device_id)`, `list_devices(filters)`, `update_device(device_id, schema)`, `delete_device(device_id)`.
  - Each method:
    1. Calls the repository for data access.
    2. Raises appropriate `AppException` subclasses for error cases (not found, already deleted).
    3. Converts SQLAlchemy model → Pydantic response schema before returning.
  - The service receives the repository (or `AsyncSession`) via constructor/dependency.
  - 🔑 Concept: Service layer pattern, model↔schema conversion, separation of concerns
  - 🧠 *Interview Q: Should the service receive an `AsyncSession` directly, or should it receive a `DeviceRepository` instance? What are the trade-offs for testability?*

---

### Task 1.11 — Device API Routes (Presentation Layer)

**Deliverable:** All 5 device CRUD endpoints are functional. Swagger UI shows accurate schemas with examples.
FR-01 through FR-05 are complete.

- [ ] **1.11.1** — Implement `api/v1/devices.py`:
  - Create an `APIRouter(prefix="/devices", tags=["Devices"])`.
  - Implement all 5 endpoints:
    - `POST /` — Register device (FR-01). Status `201 Created`.
    - `GET /` — List devices with query params (FR-02). Status `200 OK`.
    - `GET /{device_id}` — Get device by ID (FR-03). Status `200 OK`.
    - `PATCH /{device_id}` — Partial update (FR-04). Status `200 OK`.
    - `DELETE /{device_id}` — Soft delete (FR-05). Status `204 No Content`.
  - Each endpoint:
    - Uses `Depends()` to inject the service.
    - Specifies `response_model` for automatic serialization.
    - Has `summary` and `description` for OpenAPI docs.
  - 🔑 Concept: `APIRouter`, `Depends()` chaining, `response_model`, HTTP status codes, path parameters
  - 🧠 *Interview Q: Why return `201 Created` for POST instead of `200 OK`? Why `204 No Content` for DELETE instead of `200 OK`? When would you use `202 Accepted`?*

- [ ] **1.11.2** — Implement `api/v1/router.py`:
  - Create a single `v1_router` that includes all v1 sub-routers.
  - Include `v1_router` in `main.py` with `prefix="/api/v1"`.

- [ ] **1.11.3** — Implement `core/dependencies.py`:
  - Create a `get_device_service()` dependency that creates a `DeviceService` instance with the injected `AsyncSession`.
  - Create a reusable `PaginationParams` dependency using `Depends()`.
  - 🔑 Concept: Dependency injection trees in FastAPI, sub-dependencies, `Depends()` caching
  - 🧠 *Interview Q: FastAPI caches `Depends()` calls within a single request. What does this mean? How is this different from NestJS's singleton scope vs request scope?*

---

### Task 1.12 — Health Check Endpoint

**Deliverable:** `GET /health` returns system status including database connectivity. FR-23 and NFR-06 partially
satisfied.

- [ ] **1.12.1** — Implement `api/health.py`:
  - Create a `HealthResponse` schema in `schemas/common.py`: `{ "status": "healthy"|"degraded", "version": "0.1.0", "timestamp": "..." }`.
  - Implement `GET /health`:
    - Attempt a `SELECT 1` against the database.
    - Return `"healthy"` if the query succeeds, `"degraded"` if it fails.
    - Catch the database exception — do NOT crash.
  - Include the health router in `main.py` (not under `/api/v1` — health checks are unversioned).
  - 🔑 Concept: Health check patterns, graceful degradation, unversioned routes
  - 🧠 *Interview Q: Why is the health check endpoint unversioned? What's the difference between a liveness probe and a readiness probe in Kubernetes?*

---

### Task 1.13 — Manual Testing & Phase 1 Verification

**Deliverable:** All Phase 1 endpoints are tested manually via Swagger UI and/or `curl`. Edge cases are verified.

- [ ] **1.13.1** — Test the happy path for all 5 device CRUD operations via `/docs`.
- [ ] **1.13.2** — Test error cases:
  - POST with invalid data (missing fields, invalid enum values, name too short).
  - GET/PATCH/DELETE with a non-existent UUID.
  - DELETE the same device twice.
  - GET a deleted device.
- [ ] **1.13.3** — Test the filtered listing:
  - Create 5+ devices with different types, statuses, and locations.
  - Test filtering by `type`, `status`, `location`.
  - Test pagination: `?page=1&size=2`, `?page=2&size=2`.
  - Test sorting: `?sort_by=name&order=asc`.
- [ ] **1.13.4** — Verify health check:
  - Hit `GET /health` — expect `"healthy"`.
  - Stop PostgreSQL, hit `GET /health` — expect `"degraded"` (not a crash).
- [ ] **1.13.5** — Review all logs: confirm they are valid JSON with `timestamp`, `level`, `message`, `module`.

---

## Phase 2: Telemetry Ingestion & Validation

**Goal:** Implement the telemetry data pipeline — single and batch ingestion with cross-entity validation,
idempotency, and automatic device status transitions.

**What you'll learn:** Complex Pydantic validators, business rule enforcement across entities,
SQLAlchemy upsert patterns (`ON CONFLICT`), batch database operations, and `BackgroundTasks` basics.

---

### Task 2.1 — Telemetry Model & Migration

- [ ] **2.1.1** — Implement `models/telemetry.py`:
  - Define `TelemetryReading` per the ER diagram.
  - Add the **unique constraint** on `(device_id, timestamp, metric_type)` for idempotency (NFR-07).
  - Add composite index on `(device_id, timestamp DESC)` for efficient history queries.
  - 🔑 Concept: Composite unique constraints, composite indexes, index direction

- [ ] **2.1.2** — Generate and apply migration. Verify the table and constraints in PostgreSQL.

---

### Task 2.2 — Telemetry Schemas with Cross-Entity Validation

- [ ] **2.2.1** — Define the device-type to metric-type compatibility map:
  ```
  temperature_sensor → [temperature_celsius, battery_percent]
  power_meter        → [power_watts, battery_percent]
  security_camera    → [motion_detected, battery_percent]
  ```
  Decide where this mapping lives. (Hint: it's a domain/business rule, not a schema concern.)
  - 🧠 *Interview Q: Should this validation be in the Pydantic schema, the service, or the repository? Why?*

- [ ] **2.2.2** — Implement `schemas/telemetry.py`:
  - `TelemetryCreateSchema` — `timestamp` (datetime), `metric_type` (enum), `value` (float).
  - `TelemetryBatchItemSchema` — Same plus `device_id` (UUID).
  - `TelemetryBatchSchema` — `readings: list[TelemetryBatchItemSchema]` with a validator enforcing max 100 items.
  - `TelemetryResponseSchema` — Full reading representation.
  - `BatchResultSchema` — `{ "accepted": int, "rejected": int, "errors": list[...] }`.
  - 🔑 Concept: Pydantic `field_validator`, `model_validator`, list length constraints

---

### Task 2.3 — Telemetry Repository with Upsert

- [ ] **2.3.1** — Implement `repositories/telemetry_repository.py`:
  - `async create_reading(reading)` — Standard insert.
  - `async upsert_reading(reading)` — Uses PostgreSQL `INSERT ... ON CONFLICT (device_id, timestamp, metric_type) DO UPDATE SET value = EXCLUDED.value` for idempotency.
  - `async bulk_upsert(readings: list)` — Batch upsert using `executemany` or SQLAlchemy's `insert().values()` with `on_conflict_do_update`.
  - 🔑 Concept: PostgreSQL `ON CONFLICT`, SQLAlchemy `insert().on_conflict_do_update()`, batch operations
  - 🧠 *Interview Q: What is the performance difference between inserting 100 rows one-by-one in a loop vs. a single batch `INSERT`? What about using `executemany`? How does this relate to network round-trips?*

---

### Task 2.4 — Telemetry Service & Business Rules

- [ ] **2.4.1** — Implement `services/telemetry_service.py`:
  - `async ingest_reading(device_id, schema)`:
    1. Fetch the device from the repository (raise `DeviceNotFoundError` if missing or deleted).
    2. Validate metric-type compatibility with the device type.
    3. Upsert the reading.
    4. If device status is `offline`, transition to `online` (FR-08).
    5. Return the created/updated reading.
  - `async ingest_batch(schema)`:
    1. Process each reading individually, collecting successes and failures.
    2. Return `BatchResultSchema` with counts and per-item errors.
    3. Do NOT abort the entire batch if one reading fails — partial success is expected.
  - 🔑 Concept: Partial failure handling in batch operations, transactional boundaries
  - 🧠 *Interview Q: Should the batch operation run in a single database transaction or one transaction per reading? What are the trade-offs? What if reading #50 out of 100 fails?*

---

### Task 2.5 — Telemetry API Routes

- [ ] **2.5.1** — Implement `api/v1/telemetry.py`:
  - `POST /api/v1/devices/{device_id}/telemetry` — Single ingestion (FR-06). Status `201 Created`.
  - `POST /api/v1/telemetry/batch` — Batch ingestion (FR-07). Status `207 Multi-Status` (partial success possible).
  - 🔑 Concept: `207 Multi-Status` pattern, nested route design

---

### Task 2.6 — Phase 2 Verification

- [ ] **2.6.1** — Test single ingestion: valid reading, incompatible metric type, non-existent device, deleted device.
- [ ] **2.6.2** — Test idempotency: submit the same `(device_id, timestamp, metric_type)` twice — value should update, not duplicate.
- [ ] **2.6.3** — Test batch ingestion: mix of valid and invalid readings — verify `accepted`/`rejected` counts.
- [ ] **2.6.4** — Test auto-status: create a device (default `offline`), submit telemetry, verify status is now `online`.
- [ ] **2.6.5** — Test batch size limit: submit 101 readings — expect `422`.

---

## Phase 3: Authentication & Authorization

**Goal:** Implement JWT-based auth with registration, login, token refresh, and route protection. Retrofit all
existing endpoints to require authentication.

**What you'll learn:** OAuth2 password bearer flow in FastAPI, JWT creation/verification, `bcrypt` hashing,
dependency injection for auth guards, and token revocation patterns.

---

### Task 3.1 — User & RefreshToken Models

- [ ] **3.1.1** — Implement `models/user.py`: `User` model per ER diagram (email unique, hashed_password, is_active).
- [ ] **3.1.2** — Implement `models/refresh_token.py`: `RefreshToken` model (token_hash, expires_at, revoked).
- [ ] **3.1.3** — Import both in `models/__init__.py`. Generate and apply migration.

---

### Task 3.2 — Security Utilities

- [ ] **3.2.1** — Install auth dependencies: `uv add "python-jose[cryptography]" "passlib[bcrypt]"`

- [ ] **3.2.2** — Implement `core/security.py`:
  - `hash_password(plain: str) -> str` — bcrypt with work factor 12.
  - `verify_password(plain: str, hashed: str) -> bool`.
  - `create_access_token(subject: str, expires_delta: timedelta) -> str` — JWT with `sub`, `exp`, `iat` claims.
  - `create_refresh_token(subject: str) -> str` — Longer-lived JWT.
  - `decode_token(token: str) -> dict` — Verify and decode. Raise on expiry or invalid signature.
  - 🔑 Concept: JWT claims (`sub`, `exp`, `iat`), symmetric vs asymmetric signing, bcrypt work factor
  - 🧠 *Interview Q: Why hash the refresh token before storing it in the database? What attack does this prevent?*

---

### Task 3.3 — Auth Schemas, Repository, Service & Routes

- [ ] **3.3.1** — Implement `schemas/auth.py`: `UserRegisterSchema`, `UserLoginSchema`, `TokenResponse`, `RefreshTokenRequest`.
- [ ] **3.3.2** — Implement `repositories/user_repository.py`: `get_by_email()`, `create()`.
- [ ] **3.3.3** — Implement `services/auth_service.py`:
  - `register(schema)` — Check email uniqueness, hash password, create user.
  - `login(schema)` — Verify credentials, generate access + refresh tokens, store refresh token hash.
  - `refresh(token)` — Validate refresh token, check revocation, issue new access token.
  - 🔑 Concept: Auth service orchestration, token lifecycle management

- [ ] **3.3.4** — Implement `api/v1/auth.py`:
  - `POST /auth/register` (FR-19)
  - `POST /auth/login` (FR-20) — Use `OAuth2PasswordRequestForm` for Swagger UI integration.
  - `POST /auth/refresh` (FR-21)
  - 🔑 Concept: `OAuth2PasswordBearer`, `OAuth2PasswordRequestForm`, Swagger UI "Authorize" button

---

### Task 3.4 — Route Protection (Auth Guard)

- [ ] **3.4.1** — Implement `get_current_user()` in `core/dependencies.py`:
  - Use `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")` as a scheme.
  - Decode the JWT, extract `sub` (user ID), fetch the user from the database.
  - Raise `401 Unauthorized` if the token is invalid/expired or the user is inactive.
  - 🔑 Concept: FastAPI security dependencies, `Depends()` chaining for auth
  - 🧠 *Interview Q: How does `OAuth2PasswordBearer` work under the hood? It doesn't actually validate the token — what does it do?*

- [ ] **3.4.2** — Add `current_user: User = Depends(get_current_user)` to all device and telemetry endpoints.
  - Device creation should set `created_by = current_user.id`.
  - Verify via Swagger: endpoints return `401` without a token, `200` with a valid token.

---

### Task 3.5 — Phase 3 Verification

- [ ] **3.5.1** — Test registration: valid, duplicate email, weak password.
- [ ] **3.5.2** — Test login: correct credentials, wrong password, non-existent email.
- [ ] **3.5.3** — Test token flow: login → use access token → token expires → refresh → use new token.
- [ ] **3.5.4** — Test protection: hit device endpoints without a token → `401`. With expired token → `401`. With valid token → success.
- [ ] **3.5.5** — Verify Swagger UI "Authorize" button works (lock icon).

---

## Phase 4: Real-Time WebSocket Layer

**Goal:** Implement an in-process event bus and WebSocket connection manager that streams live telemetry
readings and device status changes to connected clients.

**What you'll learn:** `asyncio` event patterns, WebSocket lifecycle in FastAPI/Starlette, pub/sub design,
connection tracking, and filtered subscriptions.

---

### Task 4.1 — In-Memory Event Bus

- [ ] **4.1.1** — Implement `core/events.py`:
  - Create an `EventBus` class using `asyncio.Queue` or a subscriber-list pattern.
  - Methods: `subscribe(topic, callback)`, `unsubscribe(topic, callback)`, `publish(topic, data)`.
  - Support topics: `"telemetry"`, `"device_status"`.
  - Create a module-level singleton instance: `event_bus = EventBus()`.
  - 🔑 Concept: Observer pattern, `asyncio.Queue`, in-process pub/sub, singleton lifecycle
  - 🧠 *Interview Q: What happens to this event bus if you scale to 2 `uvicorn` worker processes? How would you solve cross-process broadcasting?*

---

### Task 4.2 — WebSocket Connection Manager

- [ ] **4.2.1** — Implement `services/websocket_service.py`:
  - Create a `ConnectionManager` class.
  - Track connections per topic in a dict: `{ "telemetry": set[WebSocket], "device_status": set[WebSocket] }`.
  - Support optional device-level filtering: `{ "telemetry:<device_id>": set[WebSocket] }`.
  - Methods: `connect(websocket, topic, device_id?)`, `disconnect(websocket, topic)`, `broadcast(topic, data, device_id?)`.
  - Handle `WebSocketDisconnect` exceptions gracefully.
  - 🔑 Concept: WebSocket connection lifecycle, Starlette `WebSocket` API, `accept()` / `send_json()` / `close()`

---

### Task 4.3 — Wire Events to WebSocket Broadcast

- [ ] **4.3.1** — In `telemetry_service.py`, after a successful ingestion, publish to the event bus:
  `event_bus.publish("telemetry", reading_data)`.
- [ ] **4.3.2** — In the connection manager, subscribe to the event bus and broadcast to relevant WebSocket clients.
- [ ] **4.3.3** — Similarly, publish `"device_status"` events when a device status changes (FR-08 transition).

---

### Task 4.4 — WebSocket Endpoints

- [ ] **4.4.1** — Implement `api/v1/websockets.py`:
  - `WS /api/v1/ws/telemetry?device_id=<optional>` — Live telemetry feed (FR-09).
  - `WS /api/v1/ws/devices/status` — Device status changes (FR-10).
  - Each endpoint: accepts the connection, registers with the manager, keeps the connection alive in a loop, handles disconnection cleanly.
  - 🔑 Concept: WebSocket route handlers, `await websocket.accept()`, message loop patterns
  - 🧠 *Interview Q: How do you authenticate a WebSocket connection? You can't send headers after the initial handshake. What are the common approaches?*

---

### Task 4.5 — Phase 4 Verification

- [ ] **4.5.1** — Use `websocat` or a browser WebSocket client to connect to `ws://localhost:8000/api/v1/ws/telemetry`.
- [ ] **4.5.2** — In another terminal, POST a telemetry reading. Verify the WebSocket client receives it in real-time.
- [ ] **4.5.3** — Connect with `?device_id=<uuid>`. POST readings for different devices. Verify only matching readings are received.
- [ ] **4.5.4** — Test disconnection: close the client, post another reading — no crash on the server.
- [ ] **4.5.5** — Test multiple clients: connect 3 clients, post a reading — all 3 receive it.

---

## Phase 5: Alert System

**Goal:** Implement a rule-based alert engine that evaluates incoming telemetry against user-defined thresholds
and creates alert events asynchronously via `BackgroundTasks`.

**What you'll learn:** FastAPI `BackgroundTasks`, rule engine design, async background processing, and the
trade-offs of in-process vs. external task queues.

---

### Task 5.1 — AlertRule & AlertEvent Models

- [ ] **5.1.1** — Implement `models/alert_rule.py` and `models/alert_event.py` per the ER diagram.
- [ ] **5.1.2** — Generate and apply migration. Verify tables and foreign keys.

---

### Task 5.2 — Alert Schemas

- [ ] **5.2.1** — Implement `schemas/alert.py`:
  - `AlertRuleCreateSchema`, `AlertRuleResponseSchema`, `AlertEventResponseSchema`, `AlertAcknowledgeSchema`.
  - Validate: `threshold` must be a finite number (not NaN/Infinity). `operator` must be valid enum.

---

### Task 5.3 — Alert Repository

- [ ] **5.3.1** — Implement `repositories/alert_rule_repository.py`: CRUD + `get_active_rules()`.
- [ ] **5.3.2** — Implement `repositories/alert_event_repository.py`: create, filtered listing, acknowledge.

---

### Task 5.4 — Alert Service & Rule Engine

- [ ] **5.4.1** — Implement `services/alert_service.py`:
  - `create_rule(schema, user_id)` — CRUD for alert rules (FR-12).
  - `evaluate_reading(reading, device)` — Core rule engine:
    1. Fetch all active rules matching the reading's `metric_type`.
    2. Optionally filter by `device_type`.
    3. Evaluate each rule: compare `reading.value` against `rule.threshold` using `rule.operator`.
    4. For each match, create an `AlertEvent`.
  - `acknowledge_alert(alert_id, user_id)` — Set acknowledged (FR-15).
  - 🔑 Concept: Rule engine pattern, operator dispatch (dict mapping operators to comparison functions)
  - 🧠 *Interview Q: How would you make the rule engine extensible if you needed to add compound rules (e.g., "temperature > 80 AND battery < 10%")?*

---

### Task 5.5 — Background Alert Evaluation

- [ ] **5.5.1** — Integrate `BackgroundTasks` into the telemetry ingestion endpoint:
  - After successfully ingesting a reading, add `alert_service.evaluate_reading` as a background task.
  - The background task receives the reading data and runs the rule engine.
  - The ingestion response returns **immediately** — alert evaluation does not block it (FR-13).
  - 🔑 Concept: `BackgroundTasks` in FastAPI, async vs sync background tasks, task lifecycle
  - 🧠 *Interview Q: What happens if the background task fails (e.g., database error during alert creation)? Does the telemetry ingestion response still succeed? Is this a problem? How would you handle it?*

---

### Task 5.6 — Alert API Routes

- [ ] **5.6.1** — Implement `api/v1/alerts.py`:
  - `POST /alerts/rules` — Create rule (FR-12).
  - `GET /alerts` — List triggered alerts with filters (FR-14).
  - `PATCH /alerts/{alert_id}/acknowledge` — Acknowledge (FR-15).
  - All protected by auth.

---

### Task 5.7 — Phase 5 Verification

- [ ] **5.7.1** — Create a rule: "temperature_celsius > 80, severity=critical".
- [ ] **5.7.2** — Ingest a reading with `temperature_celsius = 85`. Verify an alert event was created.
- [ ] **5.7.3** — Ingest a reading with `temperature_celsius = 50`. Verify NO alert was created.
- [ ] **5.7.4** — List alerts filtered by severity, device, acknowledged status.
- [ ] **5.7.5** — Acknowledge an alert. Verify `acknowledged_at` and `acknowledged_by` are set.
- [ ] **5.7.6** — Verify the ingestion response time is NOT delayed by alert evaluation (check logs for timing).

---

## Phase 6: Analytics & Polish

**Goal:** Implement aggregation queries, dashboard stats, telemetry history, rate limiting, CORS,
request correlation IDs, and polish the API documentation.

**What you'll learn:** SQL aggregation functions with SQLAlchemy, window-based grouping, FastAPI middleware,
rate limiting patterns, and OpenAPI documentation best practices.

---

### Task 6.1 — Telemetry History Endpoint

- [ ] **6.1.1** — Implement `GET /api/v1/devices/{device_id}/telemetry` (FR-16):
  - Paginated, filtered by `metric_type`, `from_date`, `to_date`.
  - Sorted by `timestamp DESC`.
  - Reuse `PaginatedResponse[TelemetryResponseSchema]`.

---

### Task 6.2 — Aggregated Statistics

- [ ] **6.2.1** — Implement `repositories/analytics_repository.py`:
  - Build a query using `func.min()`, `func.max()`, `func.avg()`, `func.count()`.
  - Group by `device_id` and `metric_type`.
  - Support time-window grouping: `hourly` (truncate timestamp to hour), `daily`, `weekly`.
  - 🔑 Concept: `func.date_trunc()` in PostgreSQL via SQLAlchemy, GROUP BY with aggregates

- [ ] **6.2.2** — Implement `schemas/analytics.py`: `AggregatedMetricSchema`, `DashboardStatsSchema`.

- [ ] **6.2.3** — Implement `services/analytics_service.py` and `api/v1/analytics.py`:
  - `GET /api/v1/analytics/summary` (FR-17).
  - `GET /api/v1/analytics/dashboard` (FR-18).
  - 🧠 *Interview Q: These aggregation queries can be expensive on large datasets. How would you optimize them? (Hint: materialized views, caching, pre-computed aggregates)*

---

### Task 6.3 — Request Correlation ID Middleware

- [ ] **6.3.1** — Create a middleware in `core/logging.py` (or a separate file):
  - On each request, check for `X-Request-ID` header. If absent, generate a UUID.
  - Store the correlation ID in a `contextvars.ContextVar` so it's accessible from any async function.
  - Include it in every log entry.
  - Return it in the response headers.
  - 🔑 Concept: `contextvars` in Python (equivalent to `AsyncLocalStorage` in Node.js), middleware patterns
  - 🧠 *Interview Q: Why `contextvars` instead of thread-local storage? What problem does `contextvars` solve in async Python?*

---

### Task 6.4 — CORS Configuration

- [ ] **6.4.1** — Add `CORSMiddleware` in `main.py`:
  - Load allowed origins from `settings.CORS_ALLOWED_ORIGINS`.
  - Configure `allow_methods`, `allow_headers`, `allow_credentials`.
  - 🔑 Concept: Same-origin policy, CORS preflight requests, credential handling

---

### Task 6.5 — Rate Limiting

- [ ] **6.5.1** — Implement rate limiting on auth endpoints (NFR-11):
  - Use `slowapi` or a custom in-memory rate limiter (dict of IP → request timestamps).
  - Limit: 5 login attempts per minute per IP.
  - Return `429 Too Many Requests` with `Retry-After` header.
  - 🔑 Concept: Token bucket vs sliding window rate limiting, IP-based limiting
  - 🧠 *Interview Q: In-memory rate limiting doesn't work behind a load balancer with multiple instances. How would you solve this? (Hint: Redis, distributed rate limiting)*

---

### Task 6.6 — Enhance Device Details with Latest Telemetry

- [ ] **6.6.1** — Update `GET /api/v1/devices/{device_id}` (FR-03) to include the latest telemetry reading:
  - Add a subquery or join to fetch the most recent reading for the device.
  - Extend `DeviceResponseSchema` with an optional `latest_reading` field.

---

### Task 6.7 — API Documentation Polish

- [ ] **6.7.1** — Ensure every endpoint has:
  - `summary` — Short one-liner.
  - `description` — Detailed explanation with example use cases.
  - `response_model` — Accurate schema.
  - `responses` — Document error responses (`404`, `422`, `401`, `429`).
  - `tags` — Grouped by domain (`Devices`, `Telemetry`, `Alerts`, `Analytics`, `Auth`, `System`).
  - Example payloads in Pydantic schemas via `json_schema_extra`.
- [ ] **6.7.2** — Verify Swagger UI (`/docs`) and ReDoc (`/redoc`) render correctly.

---

### Task 6.8 — Test Suite

- [ ] **6.8.1** — Install test dependencies: `uv add --dev pytest pytest-asyncio httpx pytest-cov`

- [ ] **6.8.2** — Implement `tests/conftest.py`:
  - Create a test database (separate from development).
  - Set up async test client using `httpx.AsyncClient` + `ASGITransport`.
  - Create factory fixtures for test data (users, devices, readings).
  - 🔑 Concept: Test isolation, database fixtures, fixture scoping (`session`, `function`)

- [ ] **6.8.3** — Write unit tests for services:
  - `test_device_service.py` — CRUD operations, error cases, soft-delete behavior.
  - `test_telemetry_service.py` — Ingestion, validation, batch processing, idempotency.
  - `test_alert_service.py` — Rule evaluation logic, edge cases.
  - `test_auth_service.py` — Registration, login, token validation.

- [ ] **6.8.4** — Write integration tests for API endpoints:
  - `test_device_endpoints.py` — Full HTTP lifecycle for devices.
  - `test_telemetry_endpoints.py` — Ingestion workflows.
  - `test_alert_endpoints.py` — Rule creation → alert triggering → acknowledgment.
  - `test_auth_endpoints.py` — Registration → login → protected access.
  - `test_websocket_endpoints.py` — WebSocket connection, message reception.

- [ ] **6.8.5** — Run full suite with coverage: `uv run pytest --cov=fastapi_app --cov-report=term-missing`.
  Target: 80%+ coverage.

---

### Task 6.9 — Final Phase 6 Verification

- [ ] **6.9.1** — Full end-to-end walkthrough:
  1. Register a user.
  2. Login, get tokens.
  3. Create 3 devices (one of each type).
  4. Create alert rules.
  5. Ingest telemetry (some normal, some anomalous).
  6. Verify alerts were triggered in background.
  7. Connect WebSocket client — verify live stream.
  8. Query analytics — verify aggregations.
  9. Acknowledge alerts.
  10. Soft-delete a device — verify telemetry preserved.
- [ ] **6.9.2** — Run the full test suite — all green, 80%+ coverage.
- [ ] **6.9.3** — Run `ruff check .` and `ruff format --check .` — no issues.
- [ ] **6.9.4** — Final review of `/docs` — all schemas, examples, and descriptions are accurate.

---

## Post-Project: Interview Preparation Topics

Once the project is complete, use it as a reference to discuss these topics in interviews:

### System Design Discussion Points
- [ ] How would you scale this to 10,000 devices sending telemetry every second?
- [ ] When would you introduce Redis for WebSocket broadcasting?
- [ ] When would you replace `BackgroundTasks` with Celery?
- [ ] How would you decompose this monolith into microservices? Which boundaries?
- [ ] How would you handle time-series data at scale (TimescaleDB, ClickHouse)?

### Code Quality Discussion Points
- [ ] Explain your dependency injection tree (draw it on a whiteboard).
- [ ] Walk through a request lifecycle from HTTP → route → service → repo → DB → response.
- [ ] Explain how Pydantic validation prevents invalid data from reaching the database.
- [ ] Discuss your error handling strategy and why structured errors matter.
- [ ] Explain the difference between SQLAlchemy models and Pydantic schemas.

### Python-Specific Discussion Points
- [ ] `async/await` in Python vs Node.js — what's the GIL's role?
- [ ] `contextvars` vs thread-local storage — when to use each.
- [ ] Type annotations and `mypy` — Python's approach to type safety.
- [ ] Why `uv` over `pip` + `virtualenv`?
