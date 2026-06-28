<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black" alt="Render"/>
</p>

<h1 align="center">Insight API</h1>

<p align="center">
  Production-ready event analytics backend for tracking business events and powering dashboards.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-overview">API</a> •
  <a href="#deployment">Deploy</a>
</p>

---

## Project Overview

**Insight API** is a backend analytics service that receives business events from applications (`user_registered`, `order_created`, `payment_completed`, etc.), stores them in PostgreSQL, and exposes rich analytics endpoints for dashboards and reporting.

Built as a **portfolio-grade** project — clean architecture, production patterns, professional Swagger docs, Docker, and Render deployment.

> This is not a CRUD tutorial. It demonstrates how a real analytics ingestion API is structured.

---

## Features

- **Event Ingestion** — single and batch endpoints with idempotency support
- **API Key Authentication** — secure hashed keys for SDK/backend ingestion
- **JWT Dashboard Auth** — 2-hour access tokens for analytics and management
- **Rich Analytics** — overview, time series, breakdown, DAU/WAU/MAU, funnels, property stats
- **CSV / JSON Export** — download event data for external tools
- **PostgreSQL Aggregations** — `date_trunc`, `COUNT DISTINCT`, window functions
- **Layered Architecture** — api → services → repositories → models
- **Alembic Migrations** — version-controlled schema
- **Docker Ready** — root `Dockerfile`, `entrypoint.sh`, auto-migrations via asyncpg
- **Professional OpenAPI** — tagged endpoints with descriptions and examples

---

## Architecture

```
┌──────────────┐     API Key      ┌─────────────────┐
│  Client Apps │ ────────────────► │  POST /events   │
│  (SDKs)      │                   │  (ingestion)    │
└──────────────┘                   └────────┬────────┘
                                            │
┌──────────────┐     JWT            ┌───────▼────────┐
│  Dashboard   │ ────────────────► │  /analytics    │
└──────────────┘                   └───────┬────────┘
                                            │
                                   ┌────────▼────────┐
                                   │   PostgreSQL    │
                                   └─────────────────┘
```

**Layers:**

| Layer | Responsibility |
|-------|---------------|
| `api/` | HTTP routing, auth deps, request/response |
| `services/` | Business logic, validation |
| `repositories/` | Data access, SQL aggregations |
| `models/` | SQLAlchemy ORM entities |

---

## Folder Structure

```
insight-api/
├── app/
│   ├── api/v1/          # Route handlers (auth, events, analytics, health)
│   ├── core/            # Config, security, exceptions
│   ├── db/              # Engine, session, base
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic v2 DTOs
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic
│   └── middleware/      # Request ID tracing
├── alembic/             # Database migrations
├── Dockerfile           # Production container image
├── entrypoint.sh        # DB wait, migrations, uvicorn
├── scripts/             # Admin creation, demo seed
├── tests/               # pytest suite
├── docker-compose.yml
└── render.yaml
```

---

## Database Schema

### `users`
Dashboard login. Single admin user (extensible).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(320) | Unique login |
| hashed_password | VARCHAR(255) | bcrypt hash |
| is_active | BOOLEAN | Account status |
| created_at | TIMESTAMPTZ | Creation time |

### `api_keys`
Ingestion credentials. Only hash stored.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Human label |
| key_prefix | VARCHAR(12) | Lookup prefix |
| key_hash | VARCHAR(64) | SHA-256 hash |
| is_active | BOOLEAN | Active status |
| last_used_at | TIMESTAMPTZ | Last ingestion |
| created_at | TIMESTAMPTZ | Creation time |

### `events`
Core analytics data. Append-only.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| event_name | VARCHAR(100) | e.g. `user_registered` |
| event_id | VARCHAR(255) | Client idempotency key |
| user_id | VARCHAR(255) | External user ID |
| session_id | VARCHAR(255) | Session identifier |
| properties | JSONB | Event payload |
| metadata | JSONB | SDK version, source |
| occurred_at | TIMESTAMPTZ | Business timestamp |
| received_at | TIMESTAMPTZ | Server receive time |
| created_at | TIMESTAMPTZ | DB insert time |

---

## Authentication Flow

### Dashboard (JWT)

```
POST /api/v1/auth/login  →  { access_token, token_type, expires_in_hours }
GET  /api/v1/auth/me     →  Authorization: Bearer <token>
```

Token expires in **2 hours**. No refresh token — re-login required.

### Event Ingestion (API Key)

```
POST /api/v1/api-keys    →  Create key (shown once)
POST /api/v1/events      →  Authorization: Bearer ins_<key>
```

Keys are prefixed with `ins_`, stored as SHA-256 hash. Full key returned only on create/rotate.

---

## API Overview

| Tag | Endpoints | Auth |
|-----|-----------|------|
| **Health** | `GET /health`, `GET /health/ready` | — |
| **Authentication** | `POST /auth/login`, `GET /auth/me` | JWT |
| **API Keys** | `GET/POST/DELETE /api-keys`, `POST /api-keys/{id}/rotate` | JWT |
| **Events** | `POST /events`, `POST /events/batch`, `GET /events` | API Key / JWT |
| **Analytics** | overview, timeseries, breakdown, funnel, export, ... | JWT |

Full interactive docs: **`/docs`**

---

## Swagger Preview

After starting the server, open [http://localhost:8000/docs](http://localhost:8000/docs)

Swagger includes:
- Tagged endpoint groups
- Request/response examples
- Status code documentation
- Authentication schemes

---

## Analytics Examples

### Overview

```bash
curl "http://localhost:8000/api/v1/analytics/overview?from=2026-01-01T00:00:00Z&to=2026-06-28T23:59:59Z" \
  -H "Authorization: Bearer <jwt>"
```

### Time Series

```bash
curl "http://localhost:8000/api/v1/analytics/timeseries?from=2026-06-01T00:00:00Z&to=2026-06-28T23:59:59Z&granularity=day" \
  -H "Authorization: Bearer <jwt>"
```

### Funnel

```bash
curl -X POST http://localhost:8000/api/v1/analytics/funnel \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": ["user_registered", "subscription_started", "payment_completed"],
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-06-28T23:59:59Z",
    "window_days": 7
  }'
```

### Ingest Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer ins_<your_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "user_registered",
    "user_id": "user_42",
    "properties": {"plan": "pro", "source": "web"}
  }'
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose

### 1. Clone & Configure

```bash
git clone https://github.com/artyomwhite/insight-api.git
cd insight-api
cp .env.example .env
```

### 2. Start with Docker

```bash
docker compose up --build
```

API: [http://localhost:8000](http://localhost:8000)  
Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Create Admin & Seed Demo Data

```bash
docker compose exec api python scripts/create_admin.py
docker compose exec api python scripts/seed_demo_events.py
```

### 4. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@insight.dev", "password": "changeme123!"}'
```

---

## Docker

Production container (`./Dockerfile` + `./entrypoint.sh`):

- **Python 3.11-slim** base image
- **asyncpg** driver only (no psycopg2)
- **Auto-migrations** — `alembic upgrade head` on container start
- **Health check** — `GET /api/v1/health`
- Binds to `$PORT` (Render) or `8000` locally

```bash
# Local
docker compose up --build

# Manual build
docker build -f ./Dockerfile -t insight-api .
docker run -p 8000:8000 -e PORT=8000 --env-file .env insight-api
```

**Startup flow** (`./entrypoint.sh`):

1. `python scripts/wait_for_db.py` — async connection check
2. `alembic upgrade head` — async migrations
3. `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Render Deployment

1. Push repo to GitHub
2. Create **Web Service** on [Render](https://render.com) — uses root `./Dockerfile` automatically
3. Set environment variables:
   - `DATABASE_URL` — Neon connection string (see below)
   - `SECRET_KEY` — auto-generated or custom
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `CORS_ORIGINS`
   - `ENVIRONMENT=production`

Render injects `PORT` automatically. Do **not** hardcode port `8000` in production.

### Neon `DATABASE_URL` example

```
postgresql+asyncpg://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
```

The app normalizes `postgres://` / `postgresql://` → `postgresql+asyncpg://` and converts `sslmode=require` → `ssl=require` for asyncpg.

After deploy (Render Shell or one-off job):

```bash
python scripts/create_admin.py
python scripts/seed_demo_events.py
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL URL (**asyncpg only**, no psycopg2) |
| `PORT` | `8000` (local) | Set by Render in production |
| `SECRET_KEY` | — | JWT signing key |
| `ENVIRONMENT` | `development` | `development` / `production` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `2` | JWT lifetime |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed origins |
| `ADMIN_EMAIL` | `admin@insight.dev` | Seed admin email |
| `ADMIN_PASSWORD` | `changeme123!` | Seed admin password |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_ANALYTICS_RANGE_DAYS` | `365` | Max query range |
| `MAX_BATCH_EVENTS` | `100` | Batch ingest limit |

---

## Testing

```bash
# Start test database
docker compose up db -d

# Create test DB
docker compose exec db psql -U insight -c "CREATE DATABASE insight_test;"

# Run tests
TEST_DATABASE_URL=postgresql+asyncpg://insight:insight@localhost:5432/insight_test pytest -v
```

Coverage: auth flow, event ingestion (single, batch, idempotency), analytics endpoints.

---

## Screenshots

> Add screenshots of Swagger UI and analytics responses after deployment.

| Swagger UI | Analytics Overview |
|------------|-------------------|
| `/docs` | `GET /analytics/overview` |

---

## Future Improvements

- [ ] Redis rate limiting for ingestion
- [ ] Materialized views for daily aggregates
- [ ] Table partitioning by month on `events`
- [ ] Webhook notifications on event thresholds
- [ ] Grafana integration
- [ ] SDK clients (Python, JavaScript)
- [ ] Real-time analytics via WebSockets
- [ ] ClickHouse for billion-scale events

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.12 | Runtime |
| FastAPI | Web framework |
| PostgreSQL 15 | Primary database |
| SQLAlchemy 2.x | ORM (async) |
| Alembic | Migrations |
| Pydantic v2 | Validation & schemas |
| JWT | Dashboard auth |
| Docker | Containerization |
| Render | Cloud deployment |
| pytest | Testing |

---

## License

MIT

---

<p align="center">Built for portfolio · GitHub · Upwork · Technical interviews</p>
