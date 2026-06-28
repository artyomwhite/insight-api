"""Event ingestion and query schemas."""

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import EVENT_NAME_PATTERN


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_name: str = Field(
        min_length=2,
        max_length=100,
        examples=["user_registered"],
        description="Snake_case event identifier",
    )
    event_id: str | None = Field(
        default=None,
        max_length=255,
        examples=["evt_abc123"],
        description="Client idempotency key",
    )
    user_id: str | None = Field(default=None, max_length=255, examples=["user_42"])
    session_id: str | None = Field(default=None, max_length=255, examples=["sess_xyz"])
    properties: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"plan": "pro", "amount": 29.99}],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"sdk_version": "1.0.0", "source": "web"}],
    )
    occurred_at: datetime | None = Field(
        default=None,
        examples=["2026-06-01T12:00:00Z"],
        description="Business timestamp; defaults to server time",
    )

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        if not re.match(EVENT_NAME_PATTERN, v):
            raise ValueError(
                "event_name must be snake_case: lowercase letters, digits, underscores"
            )
        return v


class EventBatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[EventCreate] = Field(min_length=1, max_length=100)


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_name: str
    event_id: str | None
    user_id: str | None
    session_id: str | None
    properties: dict[str, Any]
    metadata: dict[str, Any]
    occurred_at: datetime
    received_at: datetime
    created_at: datetime


class EventBatchResponse(BaseModel):
    created: int
    events: list[EventResponse]


class EventListParams(BaseModel):
    event_name: str | None = None
    user_id: str | None = None
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
