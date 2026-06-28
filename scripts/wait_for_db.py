"""Wait until PostgreSQL is reachable (asyncpg)."""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    url = settings.database_url

    if not url:
        print("ERROR: DATABASE_URL is not set")
        sys.exit(1)

    # Log host only — never credentials
    host_part = url.split("@")[-1] if "@" in url else "unknown"
    print(f"Waiting for database at {host_part}...")

    for attempt in range(1, 31):
        try:
            engine = create_async_engine(url, pool_pre_ping=True)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("Database is ready")
            return
        except Exception as exc:
            print(f"Attempt {attempt}/30: {exc}")
            await asyncio.sleep(2)

    print("ERROR: Database not reachable after 30 attempts")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
