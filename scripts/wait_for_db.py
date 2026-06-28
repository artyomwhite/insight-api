"""Wait until PostgreSQL is reachable (asyncpg via SQLAlchemy async engine)."""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.db.database_url import get_connect_args


async def wait_for_database() -> None:
    settings = get_settings()
    url = settings.database_url

    if not url:
        print("ERROR: DATABASE_URL is not set")
        sys.exit(1)

    host_part = url.split("@")[-1] if "@" in url else "unknown"
    print(f"Waiting for database at {host_part}...")

    connect_args = get_connect_args(url)

    for attempt in range(1, 31):
        try:
            engine = create_async_engine(
                url,
                connect_args=connect_args,
                pool_pre_ping=True,
            )
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("Database is ready")
            return
        except Exception as exc:
            print(f"Attempt {attempt}/30: {exc}")
            if attempt < 30:
                await asyncio.sleep(2)

    print("ERROR: Database not reachable after 30 attempts")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(wait_for_database())
