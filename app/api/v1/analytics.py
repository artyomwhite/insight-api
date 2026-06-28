"""Analytics endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse, Response

from app.api.deps import get_analytics_service, get_current_user
from app.schemas.analytics import (
    ActiveUsersResponse,
    BreakdownResponse,
    EventStatsResponse,
    FunnelRequest,
    FunnelResponse,
    OverviewResponse,
    PropertyAnalyticsResponse,
    TimeseriesResponse,
    TopPropertiesResponse,
    TopUsersResponse,
    UserTimelineResponse,
)
from app.schemas.auth import UserResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Analytics overview",
    description="High-level metrics: total events, unique users, today's count, top events.",
)
async def overview(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from", description="Start date (ISO 8601)"),
    to_date: datetime = Query(alias="to", description="End date (ISO 8601)"),
    event_name: str | None = Query(default=None),
) -> OverviewResponse:
    return await service.overview(from_date, to_date, event_name)


@router.get(
    "/timeseries",
    response_model=TimeseriesResponse,
    summary="Event time series",
    description="Event counts over time using PostgreSQL date_trunc aggregation.",
)
async def timeseries(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    granularity: str = Query(default="day", description="hour | day | week | month"),
    event_name: str | None = Query(default=None),
) -> TimeseriesResponse:
    return await service.timeseries(from_date, to_date, granularity, event_name)


@router.get(
    "/events/breakdown",
    response_model=BreakdownResponse,
    summary="Event breakdown",
    description="Event counts grouped by event_name with percentages.",
)
async def breakdown(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
) -> BreakdownResponse:
    return await service.breakdown(from_date, to_date)


@router.get(
    "/events/{event_name}",
    response_model=EventStatsResponse,
    summary="Single event statistics",
    description="Detailed stats for a specific event type.",
)
async def event_stats(
    event_name: str,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
) -> EventStatsResponse:
    return await service.event_stats(event_name, from_date, to_date)


@router.get(
    "/users/active",
    response_model=ActiveUsersResponse,
    summary="DAU / WAU / MAU",
    description="Daily, weekly, and monthly active users based on distinct user_id.",
)
async def active_users(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ActiveUsersResponse:
    return await service.active_users()


@router.get(
    "/users/{user_id}/timeline",
    response_model=UserTimelineResponse,
    summary="User event timeline",
    description="Chronological list of events for a specific user.",
)
async def user_timeline(
    user_id: str,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    limit: int = Query(default=100, ge=1, le=500),
) -> UserTimelineResponse:
    return await service.user_timeline(user_id, limit)


@router.post(
    "/funnel",
    response_model=FunnelResponse,
    summary="Conversion funnel",
    description=(
        "Calculate step-by-step conversion rates across an ordered list of events. "
        "Uses a configurable conversion window in days."
    ),
)
async def funnel(
    body: FunnelRequest,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> FunnelResponse:
    return await service.funnel(
        body.steps, body.from_date, body.to_date, body.window_days
    )


@router.get(
    "/events/{event_name}/properties/{property_key}",
    response_model=PropertyAnalyticsResponse,
    summary="Property value distribution",
    description="Top values for a JSON property within a specific event type.",
)
async def property_analytics(
    event_name: str,
    property_key: str,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
) -> PropertyAnalyticsResponse:
    return await service.property_analytics(
        event_name, property_key, from_date, to_date
    )


@router.get(
    "/top-users",
    response_model=TopUsersResponse,
    summary="Top users by event count",
    description="Users with the highest number of events in the given period.",
)
async def top_users(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    limit: int = Query(default=20, ge=1, le=100),
) -> TopUsersResponse:
    return await service.top_users(from_date, to_date, limit)


@router.get(
    "/top-properties",
    response_model=TopPropertiesResponse,
    summary="Top properties for an event",
    description="Most frequently used JSON property keys for a given event type.",
)
async def top_properties(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    event_name: str = Query(description="Event type to analyze"),
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    limit: int = Query(default=20, ge=1, le=100),
) -> TopPropertiesResponse:
    return await service.top_properties(event_name, from_date, to_date, limit)


@router.get(
    "/export",
    summary="Export events",
    description="Export events as CSV or JSON for the given date range.",
    responses={
        200: {
            "description": "Exported data",
            "content": {
                "text/csv": {},
                "application/json": {},
            },
        },
    },
)
async def export_events(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    from_date: datetime = Query(alias="from"),
    to_date: datetime = Query(alias="to"),
    event_name: str | None = Query(default=None),
    format: str = Query(default="csv", description="csv | json"),
) -> Response:
    if format == "json":
        data = await service.export_json(from_date, to_date, event_name)
        import json

        return Response(
            content=json.dumps(data, default=str),
            media_type="application/json",
        )
    csv_data = await service.export_csv(from_date, to_date, event_name)
    return PlainTextResponse(content=csv_data, media_type="text/csv")
