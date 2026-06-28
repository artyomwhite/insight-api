"""Event ingestion and query endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_api_key_auth, get_current_user, get_event_service
from app.models import ApiKey
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.event import EventBatchCreate, EventBatchResponse, EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single event",
    description=(
        "Submit one business event. Requires API key authentication. "
        "Use `event_id` for idempotent ingestion — duplicate IDs return the existing event."
    ),
    responses={
        201: {"description": "Event created"},
        200: {"description": "Duplicate event_id — existing event returned"},
        401: {"description": "Invalid API key"},
        422: {"description": "Validation error"},
    },
)
async def ingest_event(
    body: EventCreate,
    _: Annotated[ApiKey, Depends(get_api_key_auth)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> EventResponse:
    return await service.ingest_one(body)


@router.post(
    "/batch",
    response_model=EventBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest batch of events",
    description="Submit up to 100 events in a single request. Requires API key authentication.",
    responses={
        201: {"description": "Batch processed"},
        401: {"description": "Invalid API key"},
        422: {"description": "Validation error"},
    },
)
async def ingest_batch(
    body: EventBatchCreate,
    _: Annotated[ApiKey, Depends(get_api_key_auth)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> EventBatchResponse:
    return await service.ingest_batch(body.events)


@router.get(
    "",
    response_model=PaginatedResponse[EventResponse],
    summary="List events",
    description="Query stored events with filters. Requires JWT authentication.",
    responses={200: {"description": "Paginated event list"}, 401: {"description": "Unauthorized"}},
)
async def list_events(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[EventService, Depends(get_event_service)],
    event_name: str | None = Query(default=None, description="Filter by event name"),
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedResponse[EventResponse]:
    return await service.list_events(
        event_name=event_name,
        user_id=user_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event by ID",
    description="Retrieve a single event by its UUID. Requires JWT authentication.",
    responses={
        200: {"description": "Event details"},
        404: {"description": "Event not found"},
        401: {"description": "Unauthorized"},
    },
)
async def get_event(
    event_id: UUID,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[EventService, Depends(get_event_service)],
) -> EventResponse:
    return await service.get_event(event_id)
