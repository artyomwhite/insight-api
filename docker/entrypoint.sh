#!/bin/sh
set -e

echo "Waiting for database..."
python -c "
import asyncio, sys, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def wait():
    url = os.environ.get('DATABASE_URL', '')
    for i in range(30):
        try:
            engine = create_async_engine(url)
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            await engine.dispose()
            print('Database is ready')
            return
        except Exception as e:
            print(f'Attempt {i+1}/30: {e}')
            await asyncio.sleep(2)
    sys.exit(1)

asyncio.run(wait())
"

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
