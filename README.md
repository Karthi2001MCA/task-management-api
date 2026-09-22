# Task Management API

[![CI](https://github.com/Karthi2001MCA/task-management-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Karthi2001MCA/task-management-api/actions/workflows/ci.yml)

A REST API for managing tasks, built with FastAPI and PostgreSQL. Tasks have a title,
description, status and priority, and can be created, listed, retrieved, replaced and
deleted. Input is validated at the API boundary and again at the database level, and
the whole stack runs with a single command.

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 |
| Web UI | Vanilla HTML, CSS and JavaScript — no build step |
| Tests | pytest (62 tests) |
| Linting | Ruff |
| Packaging | Docker, Docker Compose |
| CI/CD | GitHub Actions → GitHub Container Registry |

---

## Architecture

```
  Client
    │  JSON over HTTP
    ▼
┌─────────────────────────────────────────────┐
│  FastAPI            routing, status codes   │  app/main.py, app/routers/
├─────────────────────────────────────────────┤
│  Pydantic           request/response schemas│  app/schemas.py
├─────────────────────────────────────────────┤
│  CRUD layer         data access, no HTTP    │  app/crud.py
├─────────────────────────────────────────────┤
│  SQLAlchemy         models, sessions        │  app/models.py, app/database.py
└─────────────────────────────────────────────┘
    │  SQL
    ▼
  PostgreSQL
```

Each boundary is a translation point. FastAPI turns HTTP into Python calls; Pydantic
turns untrusted JSON into validated objects; the CRUD layer turns those into database
operations; SQLAlchemy turns Python objects into SQL. Data becomes progressively more
trustworthy on the way in, and progressively more public on the way out.

---

## Project structure

```
task-management-api/
├── app/
│   ├── main.py            FastAPI app, /health, router registration, startup
│   ├── config.py          Settings loaded from environment
│   ├── database.py        Engine, session factory, get_db dependency
│   ├── models.py          SQLAlchemy Task model and enums
│   ├── schemas.py         Pydantic request/response schemas
│   ├── crud.py            Database operations
│   └── routers/
│       └── tasks.py       The five task endpoints
├── static/
│   ├── index.html         Browser UI
│   ├── style.css
│   └── app.js             Calls the same REST endpoints
├── tests/
│   ├── conftest.py        Fixtures: isolated test database, test client
│   └── test_tasks.py      62 tests
├── .github/workflows/
│   └── ci.yml             Lint, test, build, publish
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml         Ruff configuration
├── requirements.txt
└── .env.example
```

---

## Quick start with Docker

Requires Docker Desktop. Nothing else — no Python, no PostgreSQL.

```bash
git clone https://github.com/Karthi2001MCA/task-management-api.git
cd task-management-api
cp .env.example .env
docker compose up
```

> **The `cp .env.example .env` step is required.** Credentials are never committed, so
> a fresh clone has no `.env` and Compose has nothing to substitute. The example values
> work as-is for local use.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up
```

Then open:

- **http://localhost:8000** — the web UI
- **http://localhost:8000/docs** — interactive API documentation
- **http://localhost:8000/health** — health check

> Browse to `localhost`, not `0.0.0.0`. Uvicorn logs `Uvicorn running on http://0.0.0.0:8000`,
> but `0.0.0.0` is a *bind* address meaning "listen on every interface" — it is not a
> destination you can open in a browser.

To stop:

```bash
docker compose down        # stops containers, keeps data
docker compose down -v     # also deletes the database volume
```

### Using the published image

The image is built and published by CI on every merge to `main`:

```bash
docker pull ghcr.io/karthi2001mca/task-management-api:latest
```

Tagged `latest` and with the commit SHA, so any build is traceable to its source.

---

## Web UI

A single page served by the application itself at **http://localhost:8000**.

- Create tasks with title, description, status and priority
- Colour-coded status and priority badges; completed tasks are struck through
- Change a task's status inline — each change issues a `PUT`
- Delete with confirmation
- Filter by status
- Light and dark themes, following the operating system preference

It is plain HTML, CSS and JavaScript with no framework and no build step, served by
FastAPI from `/static`. It consumes exactly the same public endpoints any other client
would, so no API code exists solely to support it.

Validation failures are surfaced in the page rather than hidden: submitting a
two-character title shows `title: String should have at least 3 characters`, parsed
from the API's `422` response body.

---

## Local development without Docker

Requires Python 3.11 and a PostgreSQL instance.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Start PostgreSQL (a container is the simplest option):

```bash
docker run --name taskdb -e POSTGRES_USER=taskuser -e POSTGRES_PASSWORD=taskpass \
  -e POSTGRES_DB=taskdb -p 5432:5432 -d postgres:16-alpine
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup.

---

## API reference

Base URL: `http://localhost:8000`

### The Task resource

| Field | Type | Notes |
|---|---|---|
| `id` | integer | assigned by the server |
| `title` | string | required, 3–200 characters, whitespace trimmed |
| `description` | string or null | optional, max 2000 characters |
| `status` | enum | `todo` · `in_progress` · `completed` — defaults to `todo` |
| `priority` | enum | `low` · `medium` · `high` — defaults to `medium` |
| `created_at` | timestamp | set by the database |

### `POST /tasks` — create

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write the README", "priority": "high"}'
```

```json
201 Created

{
  "id": 1,
  "title": "Write the README",
  "description": null,
  "status": "todo",
  "priority": "high",
  "created_at": "2026-09-22T10:15:24.371022Z"
}
```

### `GET /tasks` — list

Returns all tasks ordered by id. An empty database returns `[]` with `200`, not `404`.

```bash
curl http://localhost:8000/tasks
```

### `GET /tasks/{id}` — retrieve

```bash
curl http://localhost:8000/tasks/1
```

```json
404 Not Found

{"detail": "Task not found"}
```

### `PUT /tasks/{id}` — replace

```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated title", "status": "completed", "priority": "low"}'
```

`PUT` replaces the whole resource. Omitted fields revert to their defaults — partial
updates would be `PATCH`, which is out of scope.

### `DELETE /tasks/{id}` — delete

```bash
curl -X DELETE http://localhost:8000/tasks/1
```

Returns `204 No Content` with an empty body.

### Status codes

| Code | When |
|---|---|
| `200` | successful `GET` or `PUT` |
| `201` | resource created |
| `204` | deleted, no body returned |
| `404` | valid request, no such task |
| `422` | malformed request — bad enum, short title, wrong type |

The distinction between `404` and `422` is deliberate: `/tasks/9999` is a well-formed
request for something that does not exist, while `/tasks/abc` is not a valid request at
all.

---

## Running tests

```bash
pytest
```

Requires a running PostgreSQL instance and a `taskdb_test` database:

```bash
docker exec -it taskdb psql -U taskuser -d taskdb -c "CREATE DATABASE taskdb_test;"
```

**62 tests** covering every endpoint, both success and failure paths, all valid and
invalid enum values, missing and malformed fields, and `404` handling across all three
verbs that can produce one.

Tests run against a **separate database**, with tables created and dropped around each
individual test. That makes them isolated and order-independent, and means running the
suite never touches development data. FastAPI's `dependency_overrides` swaps `get_db`
for a test session, so no application code is modified for testing.

Linting:

```bash
ruff check .
```

---

## CI/CD

`.github/workflows/ci.yml` runs on every push to `main` or a `feature/**` branch, and on
every pull request targeting `main`.

```
push / pull request
        │
        ├── lint-and-test
        │     ├── start postgres:16-alpine service container
        │     ├── install dependencies (pip cache)
        │     ├── ruff check .
        │     └── pytest -v
        │
        └── build-and-push        (only if the above passed)
              ├── docker build
              └── push to ghcr.io  (only from main)
```

- Tests run against **real PostgreSQL**, not SQLite, so CI exercises the same engine and
  the same native enum behaviour as production.
- `needs: lint-and-test` means a failing suite prevents publishing.
- Feature branches build the image but do not push it, catching Dockerfile errors
  without polluting the registry.
- Authentication uses the automatically provisioned `GITHUB_TOKEN`. No secret is stored
  in the repository — the main practical reason for choosing GHCR over Docker Hub.

---

## Design decisions

**Pydantic schemas are separate from SQLAlchemy models.** The model describes how a row
is stored; the schemas describe the contract with the outside world. They are separate
classes because input, output and storage are three different shapes — a client must not
send `id` or `created_at`, but must receive them. `TaskResponse` deliberately does not
inherit the input constraints, so a row that predates a validation rule can never cause
a read to fail.

**`status` and `priority` use native PostgreSQL enum types.** Invalid values are rejected
by the database as well as by the API, so the constraint holds even against direct SQL.
The cost is that adding a value requires a migration — an acceptable trade for a fixed
set.

**The CRUD layer contains no HTTP vocabulary.** `crud.get_task` returns `None` for a
missing row rather than raising a 404. Reporting the fact is the data layer's job;
deciding what it means is the router's. The same functions would work unchanged from a
CLI or a background job.

**Titles are trimmed before length validation.** A `before`-mode validator strips
whitespace so the minimum length applies to real characters — `"  ab  "` is rejected
rather than stored as a two-character title.

**`created_at` uses a server-side default.** The database clock is the single source of
truth, and the default holds for inserts that do not go through the application.

**Configuration is read from the environment, anchored to the source tree.** The same
`Settings` class reads a `.env` file locally and real environment variables inside a
container, with no code change. The path is resolved relative to the source file rather
than the working directory, so tests and containers behave identically.

---

## Known limitations

- **No authentication.** Every endpoint is public. Out of scope for this task.
- **No pagination.** `GET /tasks` returns every row; this would need limit/offset or
  cursor pagination at scale.
- **Schema created with `create_all()`, not migrations.** Fine for a fixed schema, but a
  production system would use Alembic — `create_all` never alters an existing table.
- **No `PATCH`.** Partial updates are not supported; `PUT` replaces the whole resource.
- **No `updated_at`.** The task specified six fields and no more.
- **Test and lint tooling ships in the runtime image.** Splitting `requirements.txt` from
  a `requirements-dev.txt` would reduce the image size.

---

## Verification

| Requirement | Status |
|---|---|
| CRUD endpoints | ✅ five endpoints, correct status codes |
| Database | ✅ PostgreSQL 16 via SQLAlchemy |
| Input validation | ✅ Pydantic at the API, enums and constraints at the database |
| Unit tests | ✅ 59 passing |
| Feature branches and pull requests | ✅ four branches, four merged PRs |
| Meaningful commits | ✅ Conventional Commits with explanatory bodies |
| Dockerfile | ✅ |
| docker-compose.yml | ✅ app + database, healthcheck, persistent volume |
| GitHub Actions | ✅ lint, test, build, publish |
| Image in GHCR | ✅ `ghcr.io/karthi2001mca/task-management-api` |
| No secrets committed | ✅ `.env` git-ignored, `.env.example` committed |
