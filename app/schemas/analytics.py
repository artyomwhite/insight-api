"""Analytics response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import GRANULARITY_OPTIONS


class DateRangeParams(BaseModel):
    from_date: datetime = Field(alias="from", description="Start of date range (ISO 8601)")
    to_date: datetime = Field(alias="to", description="End of date range (ISO 8601)")
    event_name: str | None = Field(default=None, description="Filter by event name")

    model_config = {"populate_by_name": True}


class OverviewResponse(BaseModel):
    total_events: int = Field(examples=[4521])
    unique_users: int = Field(examples=[312])
    events_today: int = Field(examples=[87])
    top_events: list[dict[str, Any]] = Field(
        examples=[[{"event_name": "login", "count": 1200}]]
    )
    period_from: datetime
    period_to: datetime


class TimeseriesPoint(BaseModel):
    period: datetime
    count: int


class TimeseriesResponse(BaseModel):
    granularity: str
    data: list[TimeseriesPoint]
    period_from: datetime
    period_to: datetime


class TimeseriesParams(DateRangeParams):
    granularity: str = Field(default="day", description="hour | day | week | month")

    @field_validator("granularity")
    @classmethod
    def validate_granularity(cls, v: str) -> str:
        if v not in GRANULARITY_OPTIONS:
            raise ValueError(f"granularity must be one of: {', '.join(GRANULARITY_OPTIONS)}")
        return v


class BreakdownItem(BaseModel):
    event_name: str
    count: int
    percentage: float


class BreakdownResponse(BaseModel):
    items: list[BreakdownItem]
    total: int
    period_from: datetime
    period_to: datetime


class EventStatsResponse(BaseModel):
    event_name: str
    count: int
    unique_users: int
    avg_per_day: float
    period_from: datetime
    period_to: datetime


class ActiveUsersResponse(BaseModel):
    dau: int = Field(description="Daily active users (last 24h)")
    wau: int = Field(description="Weekly active users (last 7 days)")
    mau: int = Field(description="Monthly active users (last 30 days)")
    as_of: datetime


class UserTimelineItem(BaseModel):
    id: UUID
    event_name: str
    properties: dict[str, Any]
    occurred_at: datetime


class UserTimelineResponse(BaseModel):
    user_id: str
    events: list[UserTimelineItem]
    total: int


class FunnelStep(BaseModel):
    event_name: str = Field(examples=["user_registered"])


class FunnelRequest(BaseModel):
    steps: list[str] = Field(
        min_length=2,
        max_length=10,
        examples=[["user_registered", "subscription_started", "payment_completed"]],
    )
    from_date: datetime = Field(alias="from")
    to_date: datetime = Field(alias="to")
    window_days: int = Field(default=7, ge=1, le=90, description="Conversion window in days")

    model_config = {"populate_by_name": True}


class FunnelStepResult(BaseModel):
    step: int
    event_name: str
    users: int
    conversion_rate: float
    drop_off_rate: float


class FunnelResponse(BaseModel):
    steps: list[FunnelStepResult]
    period_from: datetime
    period_to: datetime
    window_days: int


class PropertyValueItem(BaseModel):
    value: str
    count: int
    percentage: float


class PropertyAnalyticsResponse(BaseModel):
    event_name: str
    property_key: str
    items: list[PropertyValueItem]
    total: int


class TopUserItem(BaseModel):
    user_id: str
    event_count: int


class TopUsersResponse(BaseModel):
    items: list[TopUserItem]
    period_from: datetime
    period_to: datetime


class TopPropertyItem(BaseModel):
    property_key: str
    occurrence_count: int
    unique_values: int


class TopPropertiesResponse(BaseModel):
    event_name: str
    items: list[TopPropertyItem]
    period_from: datetime
    period_to: datetime
