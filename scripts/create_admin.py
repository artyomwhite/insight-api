"""Create admin user if not exists."""

import asyncio
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.models import User


async def main() -> None:
    settings = get_settings()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == settings.admin_email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Admin already exists: {settings.admin_email}")
            return

        user = User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
        )
        session.add(user)
        await session.commit()
        print(f"Admin created: {settings.admin_email}")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
