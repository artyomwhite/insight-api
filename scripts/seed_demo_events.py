"""Seed database with demo events for analytics showcase."""

import asyncio
import random
import sys
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.constants import DEMO_EVENT_TYPES
from app.core.security import generate_api_key, hash_password
from app.db.session import get_session_factory
from app.models import ApiKey, Event, User


PLANS = ["free", "starter", "pro", "enterprise"]
SOURCES = ["web", "mobile", "api"]
TASK_TYPES = ["onboarding", "report", "export", "sync"]
PAYMENT_METHODS = ["card", "paypal", "bank_transfer"]


def random_properties(event_name: str) -> dict:
    if event_name == "user_registered":
        return {"plan": random.choice(PLANS), "source": random.choice(SOURCES)}
    if event_name == "login":
        return {"source": random.choice(SOURCES), "device": random.choice(["desktop", "mobile"])}
    if event_name == "task_created":
        return {"task_type": random.choice(TASK_TYPES), "priority": random.choice(["low", "medium", "high"])}
    if event_name == "task_completed":
        return {
            "task_type": random.choice(TASK_TYPES),
            "duration_seconds": random.randint(30, 3600),
        }
    if event_name == "subscription_started":
        return {"plan": random.choice(PLANS), "billing": random.choice(["monthly", "yearly"])}
    if event_name == "payment_completed":
        return {
            "amount": round(random.uniform(9.99, 199.99), 2),
            "currency": "USD",
            "method": random.choice(PAYMENT_METHODS),
        }
    if event_name == "logout":
        return {"session_duration_minutes": random.randint(1, 120)}
    return {}


async def seed() -> None:
    settings = get_settings()
    target_count = random.randint(3000, 5000)

    session_factory = get_session_factory()
    async with session_factory() as session:
        # Admin user
        result = await session.execute(select(User).where(User.email == settings.admin_email))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
            )
            session.add(admin)
            await session.flush()
            print(f"Created admin: {settings.admin_email}")

        # Demo API key
        result = await session.execute(select(ApiKey).limit(1))
        if not result.scalar_one_or_none():
            _, prefix, key_hash = generate_api_key()
            session.add(ApiKey(name="Demo Ingestion Key", key_prefix=prefix, key_hash=key_hash))
            print("Created demo API key (check DB — use dashboard to create a usable key)")

        # Check existing events
        count_result = await session.execute(select(func.count()).select_from(Event))
        existing = count_result.scalar_one()
        if existing >= 1000:
            print(f"Database already has {existing} events — skipping seed")
            await session.commit()
            return

        # Generate users pool
        user_pool = [f"user_{uuid.uuid4().hex[:8]}" for _ in range(200)]
        now = datetime.now(UTC)
        start = now - timedelta(days=90)

        events: list[Event] = []
        for i in range(target_count):
            user_id = random.choice(user_pool)
            event_name = random.choices(
                DEMO_EVENT_TYPES,
                weights=[15, 30, 20, 18, 8, 6, 3],
            )[0]
            occurred_at = start + timedelta(
                seconds=random.randint(0, int((now - start).total_seconds()))
            )

            events.append(
                Event(
                    event_name=event_name,
                    user_id=user_id,
                    session_id=f"sess_{uuid.uuid4().hex[:12]}",
                    properties=random_properties(event_name),
                    event_metadata={"sdk_version": "1.0.0", "source": random.choice(SOURCES)},
                    occurred_at=occurred_at,
                )
            )

            if len(events) >= 500:
                session.add_all(events)
                await session.flush()
                events.clear()

        if events:
            session.add_all(events)

        await session.commit()

        final_count = await session.execute(select(func.count()).select_from(Event))
        print(f"Seed complete: {final_count.scalar_one()} total events")


if __name__ == "__main__":
    asyncio.run(seed())
    sys.exit(0)
