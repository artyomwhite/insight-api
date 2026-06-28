"""Analytics endpoint tests."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_overview(client: AsyncClient, auth_headers: dict, api_key_headers: dict):
    now = datetime.now(UTC)
    await client.post(
        "/api/v1/events",
        json={
            "event_name": "payment_completed",
            "user_id": "analytics_user_1",
            "properties": {"amount": 49.99},
            "occurred_at": now.isoformat(),
        },
        headers=api_key_headers,
    )

    from_date = (now - timedelta(days=7)).isoformat()
    to_date = (now + timedelta(hours=1)).isoformat()

    response = await client.get(
        "/api/v1/analytics/overview",
        params={"from": from_date, "to": to_date},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] >= 1
    assert "unique_users" in data
    assert "top_events" in data


@pytest.mark.asyncio
async def test_analytics_breakdown(client: AsyncClient, auth_headers: dict, api_key_headers: dict):
    await client.post(
        "/api/v1/events",
        json={"event_name": "user_registered", "user_id": "breakdown_user"},
        headers=api_key_headers,
    )

    now = datetime.now(UTC)
    response = await client.get(
        "/api/v1/analytics/events/breakdown",
        params={
            "from": (now - timedelta(days=30)).isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_analytics_active_users(
    client: AsyncClient, auth_headers: dict, api_key_headers: dict
):
    await client.post(
        "/api/v1/events",
        json={"event_name": "login", "user_id": "active_user_1"},
        headers=api_key_headers,
    )

    response = await client.get("/api/v1/analytics/users/active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "dau" in data
    assert "wau" in data
    assert "mau" in data


@pytest.mark.asyncio
async def test_analytics_funnel(client: AsyncClient, auth_headers: dict, api_key_headers: dict):
    user_id = "funnel_user_1"
    for event in ["user_registered", "subscription_started", "payment_completed"]:
        await client.post(
            "/api/v1/events",
            json={"event_name": event, "user_id": user_id},
            headers=api_key_headers,
        )

    now = datetime.now(UTC)
    response = await client.post(
        "/api/v1/analytics/funnel",
        json={
            "steps": ["user_registered", "subscription_started", "payment_completed"],
            "from": (now - timedelta(days=1)).isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
            "window_days": 7,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 3
    assert data["steps"][0]["users"] >= 1
