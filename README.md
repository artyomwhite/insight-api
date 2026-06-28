# Insight API

Production-ready **FastAPI** backend for event analytics. Deployed on [Render](https://render.com) with [Neon](https://neon.tech) PostgreSQL.

## Overview

Insight API ingests business events (`user_registered`, `order_created`, `payment_completed`, etc.), stores them in PostgreSQL, and exposes analytics endpoints for dashboards and reporting.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | Web framework + OpenAPI |
| SQLAlchemy 2.x (async) | ORM |
| asyncpg | PostgreSQL driver |
| Alembic | Database migrations |
| Neon | Managed PostgreSQL |
| Render | Cloud hosting |
| Docker | Container deployment |

## Features

- Async database layer (asyncpg only — no psycopg2)
- JWT authentication for dashboard access
- API key authentication for event ingestion
- Event ingestion (single + batch, idempotent)
- Analytics: overview, time series, funnels, DAU/WAU/MAU, export
- Auto-generated OpenAPI documentation
- Docker-based production deployment

## API Documentation

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI schema |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Liveness check |
| GET | `/api/v1/health` | Health probe |
| GET | `/api/v1/health/ready` | Readiness (DB check) |
| POST | `/api/v1/auth/login` | Dashboard login (JWT) |
| POST | `/api/v1/events` | Ingest event (API key) |
| GET | `/api/v1/analytics/overview` | Analytics overview (JWT) |

Full interactive docs: **`/docs`**

## Quick Start (Local)

```bash
git clone https://github.com/artyomwhite/insight-api.git
cd insight-api
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

```bash
# Create admin + demo data
docker compose exec api python scripts/create_admin.py
docker compose exec api python scripts/seed_demo_events.py
```

## Deployment (Render)

1. Connect GitHub repo to Render
2. Create **Web Service** — uses root `./Dockerfile`
3. Set environment variables (see below)
4. Deploy

**Startup flow** (`entrypoint.sh`):

```
wait_for_db → alembic upgrade head → uvicorn app.main:app
```

Render injects `PORT` automatically. Health check: `/api/v1/health`

## Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require` |
| `SECRET_KEY` | Yes | Random string for JWT signing |
| `ENVIRONMENT` | Yes | `production` |
| `ADMIN_EMAIL` | Yes | `admin@example.com` |
| `ADMIN_PASSWORD` | Yes | Strong password |
| `CORS_ORIGINS` | No | `https://your-frontend.com` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No | `2` (default) |

`DATABASE_URL` is auto-normalized:

- `postgres://` / `postgresql://` → `postgresql+asyncpg://`
- `sslmode=require` → SSL via asyncpg `connect_args` (Neon-compatible)

## Project Structure

```
insight-api/
├── app/                 # FastAPI application package
│   ├── api/v1/          # Route handlers
│   ├── core/            # Config, security
│   ├── db/              # Async engine, URL normalization
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access
│   └── services/        # Business logic
├── alembic/             # Migrations
├── scripts/             # Admin, seed, DB wait
├── Dockerfile           # Production image
├── entrypoint.sh        # Bootstrap script
└── render.yaml          # Render blueprint
```

## ASGI Entrypoint

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Testing

```bash
docker compose up db -d
docker compose exec db psql -U insight -c "CREATE DATABASE insight_test;"
TEST_DATABASE_URL=postgresql+asyncpg://insight:insight@localhost:5432/insight_test pytest -v
```

## Notes

- Uses **asyncpg only** — psycopg2 is not used anywhere
- OpenAPI docs (`/docs`) are enabled in all environments
- Cold start expected on Render free/starter tier
- After first deploy, run `create_admin.py` and `seed_demo_events.py` via Render Shell

## License

MIT
