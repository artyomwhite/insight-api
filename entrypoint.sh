#!/bin/sh
set -e

python scripts/wait_for_db.py

echo "Running migrations..."
alembic upgrade head

PORT="${PORT:-8000}"
echo "Starting server on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
