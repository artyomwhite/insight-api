"""Event ingestion and query business logic."""

import json
from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models import Event
from app.repositories.event_repo import EventRepository
from app.schemas.common import PaginatedResponse
from app.schemas.event import EventBatchResponse, EventCreate, EventResponse


class EventService:
    def __init__(self, event_repo: EventRepository) -> None:
        self.event_repo = event_repo
        self.settings = get_settings()

    async def ingest_one(self, data: EventCreate) -> EventResponse:
        event = await self._build_event(data)
        if data.event_id:
            existing = await self.event_repo.get_by_client_event_id(data.event_id)
            if existing:
                return EventResponse.model_validate(self._to_response_dict(existing))
        created = await self.event_repo.create(event)
        return EventResponse.model_validate(self._to_response_dict(created))

    async def ingest_batch(self, events_data: list[EventCreate]) -> EventBatchResponse:
        if len(events_data) > self.settings.max_batch_events:
            raise ValidationError(
                f"Batch exceeds maximum of {self.settings.max_batch_events} events"
            )

        events: list[Event] = []
        responses: list[EventResponse] = []

        for data in events_data:
            if data.event_id:
                existing = await self.event_repo.get_by_client_event_id(data.event_id)
                if existing:
                    responses.append(
                        EventResponse.model_validate(self._to_response_dict(existing))
                    )
                    continue
            events.append(await self._build_event(data))

        if events:
            created = await self.event_repo.create_many(events)
            responses.extend(
                EventResponse.model_validate(self._to_response_dict(e)) for e in created
            )

        return EventBatchResponse(created=len(responses), events=responses)

    async def get_event(self, event_id: UUID) -> EventResponse:
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            raise NotFoundError("Event not found")
        return EventResponse.model_validate(self._to_response_dict(event))

    async def list_events(
        self,
        *,
        event_name: str | None = None,
        user_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[EventResponse]:
        events, total = await self.event_repo.list_events(
            event_name=event_name,
            user_id=user_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )
        pages = ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse(
            items=[EventResponse.model_validate(self._to_response_dict(e)) for e in events],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def _build_event(self, data: EventCreate) -> Event:
        self._validate_properties_size(data.properties)
        occurred_at = data.occurred_at or datetime.now(UTC)
        self._validate_occurred_at(occurred_at)

        return Event(
            event_name=data.event_name,
            event_id=data.event_id,
            user_id=data.user_id,
            session_id=data.session_id,
            properties=data.properties,
            event_metadata=data.metadata,
            occurred_at=occurred_at,
        )

    def _validate_properties_size(self, properties: dict) -> None:
        size_kb = len(json.dumps(properties).encode()) / 1024
        if size_kb > self.settings.max_event_properties_size_kb:
            raise ValidationError(
                f"properties exceeds {self.settings.max_event_properties_size_kb}KB limit"
            )
        if len(properties) > 50:
            raise ValidationError("properties cannot have more than 50 keys")

    def _validate_occurred_at(self, occurred_at: datetime) -> None:
        now = datetime.now(UTC)
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        if occurred_at > now + timedelta(minutes=5):
            raise ValidationError("occurred_at cannot be more than 5 minutes in the future")
        if occurred_at < now - timedelta(days=365):
            raise ValidationError("occurred_at cannot be more than 1 year in the past")

    @staticmethod
    def _to_response_dict(event: Event) -> dict:
        return {
            "id": event.id,
            "event_name": event.event_name,
            "event_id": event.event_id,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "properties": event.properties,
            "metadata": event.event_metadata,
            "occurred_at": event.occurred_at,
            "received_at": event.received_at,
            "created_at": event.created_at,
        }
