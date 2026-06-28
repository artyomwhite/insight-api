"""Analytics queries using raw SQL and PostgreSQL aggregations."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def overview(
        self, from_date: datetime, to_date: datetime, event_name: str | None = None
    ) -> dict[str, Any]:
        filter_clause = "AND event_name = :event_name" if event_name else ""
        params: dict[str, Any] = {"from_date": from_date, "to_date": to_date}
        if event_name:
            params["event_name"] = event_name

        stats_sql = text(f"""
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT user_id) AS unique_users
            FROM events
            WHERE occurred_at >= :from_date AND occurred_at <= :to_date
            {filter_clause}
        """)
        stats = (await self.db.execute(stats_sql, params)).mappings().one()

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_params = {"today_start": today_start}
        today_filter = ""
        if event_name:
            today_filter = "AND event_name = :event_name"
            today_params["event_name"] = event_name

        today_sql = text(f"""
            SELECT COUNT(*) AS events_today
            FROM events
            WHERE occurred_at >= :today_start {today_filter}
        """)
        today_count = (await self.db.execute(today_sql, today_params)).scalar_one()

        top_sql = text(f"""
            SELECT event_name, COUNT(*) AS count
            FROM events
            WHERE occurred_at >= :from_date AND occurred_at <= :to_date
            {filter_clause}
            GROUP BY event_name
            ORDER BY count DESC
            LIMIT 10
        """)
        top_rows = (await self.db.execute(top_sql, params)).mappings().all()

        return {
            "total_events": stats["total_events"],
            "unique_users": stats["unique_users"],
            "events_today": today_count,
            "top_events": [dict(r) for r in top_rows],
        }

    async def timeseries(
        self,
        from_date: datetime,
        to_date: datetime,
        granularity: str,
        event_name: str | None = None,
    ) -> list[dict[str, Any]]:
        filter_clause = "AND event_name = :event_name" if event_name else ""
        params: dict[str, Any] = {
            "from_date": from_date,
            "to_date": to_date,
            "granularity": granularity,
        }
        if event_name:
            params["event_name"] = event_name

        sql = text(f"""
            SELECT
                date_trunc(:granularity, occurred_at AT TIME ZONE 'UTC') AS period,
                COUNT(*) AS count
            FROM events
            WHERE occurred_at >= :from_date AND occurred_at <= :to_date
            {filter_clause}
            GROUP BY period
            ORDER BY period ASC
        """)
        rows = (await self.db.execute(sql, params)).mappings().all()
        return [dict(r) for r in rows]

    async def breakdown(
        self, from_date: datetime, to_date: datetime
    ) -> tuple[list[dict[str, Any]], int]:
        sql = text("""
            SELECT event_name, COUNT(*) AS count
            FROM events
            WHERE occurred_at >= :from_date AND occurred_at <= :to_date
            GROUP BY event_name
            ORDER BY count DESC
        """)
        rows = (await self.db.execute(
            sql, {"from_date": from_date, "to_date": to_date}
        )).mappings().all()

        total = sum(r["count"] for r in rows)
        items = []
        for r in rows:
            pct = (r["count"] / total * 100) if total > 0 else 0.0
            items.append({
                "event_name": r["event_name"],
                "count": r["count"],
                "percentage": round(pct, 2),
            })
        return items, total

    async def event_stats(
        self, event_name: str, from_date: datetime, to_date: datetime
    ) -> dict[str, Any]:
        sql = text("""
            SELECT
                COUNT(*) AS count,
                COUNT(DISTINCT user_id) AS unique_users
            FROM events
            WHERE event_name = :event_name
              AND occurred_at >= :from_date
              AND occurred_at <= :to_date
        """)
        row = (await self.db.execute(sql, {
            "event_name": event_name,
            "from_date": from_date,
            "to_date": to_date,
        })).mappings().one()

        days = max((to_date - from_date).days, 1)
        return {
            "event_name": event_name,
            "count": row["count"],
            "unique_users": row["unique_users"],
            "avg_per_day": round(row["count"] / days, 2),
        }

    async def active_users(self) -> dict[str, int]:
        now = datetime.now(UTC)
        periods = {
            "dau": now - timedelta(days=1),
            "wau": now - timedelta(days=7),
            "mau": now - timedelta(days=30),
        }
        result = {}
        for key, since in periods.items():
            sql = text("""
                SELECT COUNT(DISTINCT user_id)
                FROM events
                WHERE occurred_at >= :since AND user_id IS NOT NULL
            """)
            result[key] = (await self.db.execute(sql, {"since": since})).scalar_one()
        return result

    async def user_timeline(
        self, user_id: str, limit: int = 100
    ) -> tuple[list[dict[str, Any]], int]:
        count_sql = text("""
            SELECT COUNT(*) FROM events WHERE user_id = :user_id
        """)
        total = (await self.db.execute(count_sql, {"user_id": user_id})).scalar_one()

        sql = text("""
            SELECT id, event_name, properties, occurred_at
            FROM events
            WHERE user_id = :user_id
            ORDER BY occurred_at DESC
            LIMIT :limit
        """)
        rows = (await self.db.execute(sql, {"user_id": user_id, "limit": limit})).mappings().all()
        return [dict(r) for r in rows], total

    async def funnel(
        self,
        steps: list[str],
        from_date: datetime,
        to_date: datetime,
        window_days: int,
    ) -> list[dict[str, Any]]:
        """Compute funnel conversion using PostgreSQL window functions."""
        results = []
        previous_users = None

        for i, event_name in enumerate(steps):
            if i == 0:
                sql = text("""
                    SELECT COUNT(DISTINCT user_id) AS users
                    FROM events
                    WHERE event_name = :event_name
                      AND occurred_at >= :from_date
                      AND occurred_at <= :to_date
                      AND user_id IS NOT NULL
                """)
                users = (await self.db.execute(sql, {
                    "event_name": event_name,
                    "from_date": from_date,
                    "to_date": to_date,
                })).scalar_one()
            else:
                sql = text("""
                    WITH step_users AS (
                        SELECT DISTINCT e1.user_id
                        FROM events e1
                        WHERE e1.event_name = :prev_event
                          AND e1.occurred_at >= :from_date
                          AND e1.occurred_at <= :to_date
                          AND e1.user_id IS NOT NULL
                    )
                    SELECT COUNT(DISTINCT e2.user_id) AS users
                    FROM events e2
                    INNER JOIN step_users su ON e2.user_id = su.user_id
                    WHERE e2.event_name = :event_name
                      AND e2.occurred_at >= :from_date
                      AND e2.occurred_at <= :to_date
                      AND e2.occurred_at <= (
                          SELECT MIN(e3.occurred_at) + make_interval(days => :window_days)
                          FROM events e3
                          WHERE e3.user_id = e2.user_id
                            AND e3.event_name = :prev_event
                            AND e3.occurred_at >= :from_date
                      )
                """)
                users = (await self.db.execute(sql, {
                    "event_name": event_name,
                    "prev_event": steps[i - 1],
                    "from_date": from_date,
                    "to_date": to_date,
                    "window_days": window_days,
                })).scalar_one()

            if i == 0:
                conversion = 100.0 if users > 0 else 0.0
                drop_off = 0.0
            else:
                conversion = (users / previous_users * 100) if previous_users else 0.0
                drop_off = round(100.0 - conversion, 2)

            results.append({
                "step": i + 1,
                "event_name": event_name,
                "users": users,
                "conversion_rate": round(conversion, 2),
                "drop_off_rate": drop_off,
            })
            previous_users = users

        return results

    async def property_analytics(
        self,
        event_name: str,
        property_key: str,
        from_date: datetime,
        to_date: datetime,
        limit: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        sql = text("""
            SELECT
                properties->>:property_key AS value,
                COUNT(*) AS count
            FROM events
            WHERE event_name = :event_name
              AND occurred_at >= :from_date
              AND occurred_at <= :to_date
              AND properties ? :property_key
            GROUP BY value
            ORDER BY count DESC
            LIMIT :limit
        """)
        rows = (await self.db.execute(sql, {
            "event_name": event_name,
            "property_key": property_key,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        })).mappings().all()

        total = sum(r["count"] for r in rows)
        items = []
        for r in rows:
            val = str(r["value"]) if r["value"] is not None else "null"
            pct = (r["count"] / total * 100) if total > 0 else 0.0
            items.append({"value": val, "count": r["count"], "percentage": round(pct, 2)})
        return items, total

    async def top_users(
        self, from_date: datetime, to_date: datetime, limit: int = 20
    ) -> list[dict[str, Any]]:
        sql = text("""
            SELECT user_id, COUNT(*) AS event_count
            FROM events
            WHERE occurred_at >= :from_date
              AND occurred_at <= :to_date
              AND user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY event_count DESC
            LIMIT :limit
        """)
        rows = (await self.db.execute(sql, {
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        })).mappings().all()
        return [dict(r) for r in rows]

    async def top_properties(
        self,
        event_name: str,
        from_date: datetime,
        to_date: datetime,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        sql = text("""
            SELECT
                key AS property_key,
                COUNT(*) AS occurrence_count,
                COUNT(DISTINCT properties->>key) AS unique_values
            FROM events,
                 LATERAL jsonb_object_keys(properties) AS key
            WHERE event_name = :event_name
              AND occurred_at >= :from_date
              AND occurred_at <= :to_date
              AND properties != '{}'::jsonb
            GROUP BY key
            ORDER BY occurrence_count DESC
            LIMIT :limit
        """)
        rows = (await self.db.execute(sql, {
            "event_name": event_name,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        })).mappings().all()
        return [dict(r) for r in rows]

    async def export_events(
        self,
        from_date: datetime,
        to_date: datetime,
        event_name: str | None = None,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        filter_clause = "AND event_name = :event_name" if event_name else ""
        params: dict[str, Any] = {
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        }
        if event_name:
            params["event_name"] = event_name

        sql = text(f"""
            SELECT
                id, event_name, event_id, user_id, session_id,
                properties, metadata, occurred_at, received_at
            FROM events
            WHERE occurred_at >= :from_date AND occurred_at <= :to_date
            {filter_clause}
            ORDER BY occurred_at ASC
            LIMIT :limit
        """)
        rows = (await self.db.execute(sql, params)).mappings().all()
        return [dict(r) for r in rows]
