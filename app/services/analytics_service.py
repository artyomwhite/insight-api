"""Analytics business logic."""

import csv
import io
import json
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.repositories.analytics_repo import AnalyticsRepository
from app.schemas.analytics import (
    ActiveUsersResponse,
    BreakdownResponse,
    EventStatsResponse,
    FunnelResponse,
    FunnelStepResult,
    OverviewResponse,
    PropertyAnalyticsResponse,
    PropertyValueItem,
    TimeseriesPoint,
    TimeseriesResponse,
    TopPropertiesResponse,
    TopPropertyItem,
    TopUserItem,
    TopUsersResponse,
    UserTimelineItem,
    UserTimelineResponse,
)


class AnalyticsService:
    def __init__(self, analytics_repo: AnalyticsRepository) -> None:
        self.analytics_repo = analytics_repo
        self.settings = get_settings()

    def validate_date_range(self, from_date: datetime, to_date: datetime) -> None:
        if from_date >= to_date:
            raise ValidationError("from must be before to")
        max_range = timedelta(days=self.settings.max_analytics_range_days)
        if to_date - from_date > max_range:
            raise ValidationError(
                f"Date range cannot exceed {self.settings.max_analytics_range_days} days"
            )

    async def overview(
        self, from_date: datetime, to_date: datetime, event_name: str | None = None
    ) -> OverviewResponse:
        self.validate_date_range(from_date, to_date)
        data = await self.analytics_repo.overview(from_date, to_date, event_name)
        return OverviewResponse(
            **data,
            period_from=from_date,
            period_to=to_date,
        )

    async def timeseries(
        self,
        from_date: datetime,
        to_date: datetime,
        granularity: str,
        event_name: str | None = None,
    ) -> TimeseriesResponse:
        self.validate_date_range(from_date, to_date)
        rows = await self.analytics_repo.timeseries(
            from_date, to_date, granularity, event_name
        )
        return TimeseriesResponse(
            granularity=granularity,
            data=[TimeseriesPoint(**r) for r in rows],
            period_from=from_date,
            period_to=to_date,
        )

    async def breakdown(self, from_date: datetime, to_date: datetime) -> BreakdownResponse:
        self.validate_date_range(from_date, to_date)
        items, total = await self.analytics_repo.breakdown(from_date, to_date)
        return BreakdownResponse(
            items=items,
            total=total,
            period_from=from_date,
            period_to=to_date,
        )

    async def event_stats(
        self, event_name: str, from_date: datetime, to_date: datetime
    ) -> EventStatsResponse:
        self.validate_date_range(from_date, to_date)
        data = await self.analytics_repo.event_stats(event_name, from_date, to_date)
        return EventStatsResponse(**data, period_from=from_date, period_to=to_date)

    async def active_users(self) -> ActiveUsersResponse:
        data = await self.analytics_repo.active_users()
        return ActiveUsersResponse(**data, as_of=datetime.now(UTC))

    async def user_timeline(self, user_id: str, limit: int = 100) -> UserTimelineResponse:
        rows, total = await self.analytics_repo.user_timeline(user_id, limit)
        return UserTimelineResponse(
            user_id=user_id,
            events=[UserTimelineItem(**r) for r in rows],
            total=total,
        )

    async def funnel(
        self,
        steps: list[str],
        from_date: datetime,
        to_date: datetime,
        window_days: int,
    ) -> FunnelResponse:
        self.validate_date_range(from_date, to_date)
        results = await self.analytics_repo.funnel(steps, from_date, to_date, window_days)
        return FunnelResponse(
            steps=[FunnelStepResult(**r) for r in results],
            period_from=from_date,
            period_to=to_date,
            window_days=window_days,
        )

    async def property_analytics(
        self,
        event_name: str,
        property_key: str,
        from_date: datetime,
        to_date: datetime,
    ) -> PropertyAnalyticsResponse:
        self.validate_date_range(from_date, to_date)
        items, total = await self.analytics_repo.property_analytics(
            event_name, property_key, from_date, to_date
        )
        return PropertyAnalyticsResponse(
            event_name=event_name,
            property_key=property_key,
            items=[PropertyValueItem(**i) for i in items],
            total=total,
        )

    async def top_users(
        self, from_date: datetime, to_date: datetime, limit: int = 20
    ) -> TopUsersResponse:
        self.validate_date_range(from_date, to_date)
        rows = await self.analytics_repo.top_users(from_date, to_date, limit)
        return TopUsersResponse(
            items=[TopUserItem(**r) for r in rows],
            period_from=from_date,
            period_to=to_date,
        )

    async def top_properties(
        self,
        event_name: str,
        from_date: datetime,
        to_date: datetime,
        limit: int = 20,
    ) -> TopPropertiesResponse:
        self.validate_date_range(from_date, to_date)
        rows = await self.analytics_repo.top_properties(
            event_name, from_date, to_date, limit
        )
        return TopPropertiesResponse(
            event_name=event_name,
            items=[TopPropertyItem(**r) for r in rows],
            period_from=from_date,
            period_to=to_date,
        )

    async def export_csv(
        self,
        from_date: datetime,
        to_date: datetime,
        event_name: str | None = None,
    ) -> str:
        self.validate_date_range(from_date, to_date)
        rows = await self.analytics_repo.export_events(from_date, to_date, event_name)
        output = io.StringIO()
        if not rows:
            return ""
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row_copy = dict(row)
            for key in ("properties", "metadata"):
                if key in row_copy and isinstance(row_copy[key], dict):
                    row_copy[key] = json.dumps(row_copy[key])
            if "id" in row_copy:
                row_copy["id"] = str(row_copy["id"])
            for dt_key in ("occurred_at", "received_at"):
                if dt_key in row_copy and hasattr(row_copy[dt_key], "isoformat"):
                    row_copy[dt_key] = row_copy[dt_key].isoformat()
            writer.writerow(row_copy)
        return output.getvalue()

    async def export_json(
        self,
        from_date: datetime,
        to_date: datetime,
        event_name: str | None = None,
    ) -> list[dict]:
        self.validate_date_range(from_date, to_date)
        rows = await self.analytics_repo.export_events(from_date, to_date, event_name)
        for row in rows:
            if "id" in row:
                row["id"] = str(row["id"])
            for dt_key in ("occurred_at", "received_at"):
                if dt_key in row and hasattr(row[dt_key], "isoformat"):
                    row[dt_key] = row[dt_key].isoformat()
        return rows
