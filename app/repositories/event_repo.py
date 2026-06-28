"""Event data access."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, event_id: UUID) -> Event | None:
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    async def get_by_client_event_id(self, client_event_id: str) -> Event | None:
        result = await self.db.execute(
            select(Event).where(Event.event_id == client_event_id)
        )
        return result.scalar_one_or_none()

    async def create(self, event: Event) -> Event:
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def create_many(self, events: list[Event]) -> list[Event]:
        self.db.add_all(events)
        await self.db.flush()
        for event in events:
            await self.db.refresh(event)
        return events

    async def list_events(
        self,
        *,
        event_name: str | None = None,
        user_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Event], int]:
        query = select(Event)
        count_query = select(func.count()).select_from(Event)

        if event_name:
            query = query.where(Event.event_name == event_name)
            count_query = count_query.where(Event.event_name == event_name)
        if user_id:
            query = query.where(Event.user_id == user_id)
            count_query = count_query.where(Event.user_id == user_id)
        if from_date:
            query = query.where(Event.occurred_at >= from_date)
            count_query = count_query.where(Event.occurred_at >= from_date)
        if to_date:
            query = query.where(Event.occurred_at <= to_date)
            count_query = count_query.where(Event.occurred_at <= to_date)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        query = query.order_by(Event.occurred_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
