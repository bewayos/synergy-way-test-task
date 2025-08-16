# SynergyWay Celery Test App

FastAPI + Celery + RabbitMQ + PostgreSQL demo that periodically syncs users from a public API and enriches them with addresses and credit cards. The app exposes REST endpoints and a minimal HTML page to browse saved data. The whole stack is dockerized and covered with pytest tests and linters.

---

## Table of contents

- [SynergyWay Celery Test App](#synergyway-celery-test-app)
  - [Table of contents](#table-of-contents)
  - [Architecture](#architecture)
  - [Features](#features)
  - [Tech stack](#tech-stack)
  - [Repository layout](#repository-layout)
  - [Quick start](#quick-start)
  - [Configuration](#configuration)
  - [Run \& observe](#run--observe)
  - [API](#api)
    - [Health](#health)
    - [Users](#users)
    - [Get single user](#get-single-user)
  - [HTML UI](#html-ui)
  - [Celery tasks \& schedule](#celery-tasks--schedule)
  - [Testing](#testing)
  - [Code quality](#code-quality)
  - [Idempotency details](#idempotency-details)
  - [Troubleshooting](#troubleshooting)
  - [AWS notes (TBD)](#aws-notes-tbd)

---

## Architecture

```
[FastAPI (api)]  <-- same image/code -->  /docs, /users, /healthz
        | (SQLAlchemy)
     [PostgreSQL]
        |
 [Celery worker]  ---- AMQP ----> [RabbitMQ]   (broker)
 [Celery beat]    ---- schedules   result: rpc://
 [Flower] (optional UI for Celery)
```

**Why RabbitMQ**: aligns with the vacancy “plus”. We use `amqp://` broker and `rpc://` result backend (no Redis required). A fallback to Redis is documented below.

---

## Features

* Periodic data sync and enrichment via Celery Beat.

  * Users via provider API (default dummy users, configurable via ENV).
  * Addresses & Credit Cards via provider API (default dummy data, configurable via ENV).
* PostgreSQL storage; SQLAlchemy 2.0 declarative models.
* Idempotent upserts (no duplicates across retries/reruns).
* REST API with pagination & filters; OpenAPI at `/docs`.
* Minimal HTML UI at `/users/ui`.
* Structured logs to stdout.
* Pytest test suite (unit, integration, API-level).
* Docker Compose environment (api, worker, beat, db, rabbitmq, flower).
* Linters/formatters (Ruff, Black, Isort) via pre-commit.

---

## Tech stack

* **Backend**: Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0
* **Tasks**: Celery (broker: RabbitMQ, backend: RPC)
* **DB**: PostgreSQL 16
* **HTTP**: `requests`
* **Testing**: pytest, responses, pytest-cov
* **Quality**: ruff, black, isort, pre-commit
* **Runtime**: Docker, docker compose; Flower (optional)

---

## Repository layout

```
.
├── app/
│   ├── api/                         # FastAPI routers (users, health)
│   │   ├── __init__.py
│   │   ├── routes_users.py
│   ├── tasks/                       # Celery periodic & on-demand tasks
│   │   ├── __init__.py
│   │   ├── addresses.py             # Enrich missing addresses (random-data-api)
│   │   ├── credit_cards.py          # Enrich missing credit cards (random-data-api)
│   │   └── users.py                 # Sync users (jsonplaceholder)
│   ├── templates/
│   │   └── ui.html                  # Minimal HTML UI to browse saved data
│   ├── utils/
│   │   ├── __init__.py
│   │   └── masking.py               # Helpers (credit card masking)
│   ├── celery_app.py                # Celery app/config (broker, beat schedule)
│   ├── db.py                        # SQLAlchemy engine/session, init
│   ├── logging_config.py            # Structured logging setup
│   ├── main.py                      # FastAPI app factory, routes include
│   ├── models.py                    # SQLAlchemy models
│   ├── schemas.py                   # Pydantic I/O schemas
│   └── settings.py                  # Typed settings (env)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Test fixtures (DB, client, responses mocks)
│   ├── test_api.py                  # FastAPI routes (users, ui, healthz)
│   ├── test_mapping.py              # JSON → models mapping/unit tests
│   ├── test_tasks.py                # Celery tasks (smoke, retries)
│   └── test_upsert.py               # Idempotent upserts/1:1 relations
├── docker-compose.yml               # api, worker, beat, db, rabbitmq, (flower)
├── Dockerfile                       # Multi-stage build for API/worker images
├── pyproject.toml                   # Ruff/Black/Isort, pytest config
├── .pre-commit-config.yaml          # Pre-commit hooks (lint/format)
├── .env.example                     # Example environment variables
├── .env                             # Local env (excluded from VCS)
└── README.md                        # This file
```

---

## Quick start

1. Copy environment variables and adjust as needed:

```bash
cp .env.example .env
```

2. Build & run the stack:

```bash
docker compose up --build -d
```

3. Check health & docs:

* API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health: [http://localhost:8000/healthz](http://localhost:8000/healthz) → `{"status":"ok"}`
* UI: [http://localhost:8000/users/ui](http://localhost:8000/users/ui)
* RabbitMQ UI: [http://localhost:15672](http://localhost:15672)  (guest/guest)
* Flower (if enabled): [http://localhost:5555](http://localhost:5555)

---

## Configuration

Environment variables (see `.env.example`):

**Core**

* `APP_ENV` — runtime profile, default `local`.
* `LOG_LEVEL` — log level, default `INFO`.

**Database**

* `DATABASE_URL` — e.g. `postgresql+psycopg://postgres:postgres@db:5432/postgres`

**Celery**

* `CELERY_BROKER_URL` — `amqp://guest:guest@rabbitmq:5672//`
* `CELERY_RESULT_BACKEND` — `rpc://`
* `USERS_SCHEDULE_CRON` — cron for user sync (default: `*/15 * * * *`)
* `ENRICH_ADDR_CRON` — cron for address enrichment (default: `*/10 * * * *`)
* `ENRICH_CC_CRON` — cron for credit-card enrichment (default: `*/10 * * * *`)
* `ENRICH_BATCH_SIZE` — how many missing-rows to enrich per tick (default: `20`)

**Providers**

* `USERS_API_URL` — default `http://dummyjson/users`
* `ADDRESS_API_URL` — default `http://dummyjson/users`
* `CREDIT_CARD_API_URL` — default `http://dummyjson/users`

**Fallback to Redis (optional)**

* Set `CELERY_BROKER_URL=redis://redis:6379/0` and `CELERY_RESULT_BACKEND=redis://redis:6379/1`
* No code change needed; only environment.

---

## Run & observe

Start services in foreground to see logs:

```bash
docker compose up --build
```

Common logs:

* `api` — FastAPI + uvicorn logs
* `worker` — Celery worker logs
* `beat` — Celery beat schedule logs
* `rabbitmq` — broker
* `flower` — optional Celery UI

Trigger tasks manually (examples):

```bash
# Call a task from inside the 'worker' container
docker compose exec worker celery -A app.celery_app.celery call app.tasks.users.sync_users

docker compose exec worker celery -A app.celery_app.celery call app.tasks.addresses.enrich_missing_addresses --args "[20]"

docker compose exec worker celery -A app.celery_app.celery call app.tasks.credit_cards.enrich_missing_cards --args "[20]"
```

---

## API

### Health

```
GET /healthz → {"status":"ok"}
```

### Users

```
GET /users
  Query params:
    - limit: int = 20 (1..100)
    - offset: int = 0 (>=0)
    - has_address: bool | None
    - has_card: bool | None
```

### Get single user

```
GET /users/{id}
  404 if not found
  credit_cards are masked in responses: **** **** **** 1234
```

Examples (curl):

```bash
curl -s "http://localhost:8000/users?limit=10&has_address=true"

curl -s "http://localhost:8000/users/1"
```

OpenAPI/Swagger: `http://localhost:8000/docs`

---

## HTML UI

```
GET /users/ui → HTML page (Jinja2 template) with a simple list of users
```

This is a convenience page to demonstrate that data is being saved without building a frontend.

---

## Celery tasks & schedule

* `sync_users()` — pulls users and upserts by `external_id`.
* `enrich_missing_addresses(batch_size)` — fetches random addresses and links **1:1** to users missing an address.
* `enrich_missing_cards(batch_size)` — fetches random credit cards and links **1:1** to users missing a card.

**Reliability**

* `autoretry_for=(RequestException,)`
* `retry_backoff=True`, `retry_jitter=True`
* structured JSON logs

**Idempotency**

* `users.external_id` — `UNIQUE` (upsert on conflict)
* `addresses.user_id`, `credit_cards.user_id` — `UNIQUE` (update on conflict)

Schedules are configured in `app/celery_app.py` using ENV (CRON strings). See [Configuration](#configuration).

---

## Testing

Run tests inside Docker image:

```bash
docker compose build api
docker compose run --rm api pytest -vv
```

The suite includes:

* `tests/test_mapping.py` — ORM ↔ Pydantic mapping.
* `tests/test_tasks.py` — smoke & retry paths for Celery.
* `tests/test_upsert.py` — idempotent upsert behavior.
* `tests/test_api.py` — API endpoints (`/users`, `/users/{id}`, `/users/ui`, `/healthz`).

Set `TEST_DATABASE_URL` for API tests if needed (defaults to in-memory SQLite):

```
TEST_DATABASE_URL=sqlite+pysqlite:///:memory:
```

Coverage example:

```bash
docker compose run --rm api pytest -q --cov=app --cov-report=term-missing
```

---

## Code quality

Run linters/formatters locally:

```bash
pre-commit install
pre-commit run -a
```

Tools configured in `pyproject.toml` and `.pre-commit-config.yaml`:

* ruff (lint), black (format), isort (imports)

---

## Idempotency details

* **Users** upserted by `external_id` to avoid duplicates across periodic runs.
* **Addresses/Cards** use `UNIQUE (user_id)` to ensure 1:1 relation; enrichment tasks only pick users missing related rows.
* Tasks are safe to rerun; conflicts result in updates rather than duplicates.

---

## Troubleshooting

**RabbitMQ issues**

* Check broker connectivity from worker:

  ```bash
  docker compose exec worker bash -lc "python - <<'PY'\nimport os\nprint(os.getenv('CELERY_BROKER_URL'))\nPY"
  ```
* Inspect RabbitMQ UI at [http://localhost:15672](http://localhost:15672) (guest/guest).

**Beat shows but tasks do not fire**

* Verify CRON strings in `.env`.
* Ensure `include=["app.tasks.users", "app.tasks.addresses", "app.tasks.credit_cards"]` is set in `app/celery_app.py`.

**API returns empty lists**

* Trigger `sync_users` once manually to seed users, then run enrichment tasks.

**Switch to Redis (fallback)**

* Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` to Redis URLs. Restart `worker` and `beat`.

---

## AWS notes (TBD)

---

**License**: MIT
