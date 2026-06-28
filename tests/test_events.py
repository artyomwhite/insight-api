"""Event ingestion tests."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_single_event(client: AsyncClient, api_key_headers: dict):
    response = await client.post(
        "/api/v1/events",
        json={
            "event_name": "user_registered",
            "user_id": "user_test_1",
            "properties": {"plan": "pro"},
            "occurred_at": datetime.now(UTC).isoformat(),
        },
        headers=api_key_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_name"] == "user_registered"
    assert data["user_id"] == "user_test_1"


@pytest.mark.asyncio
async def test_ingest_idempotency(client: AsyncClient, api_key_headers: dict):
    payload = {
        "event_name": "login",
        "event_id": "evt_unique_123",
        "user_id": "user_test_2",
    }
    r1 = await client.post("/api/v1/events", json=payload, headers=api_key_headers)
    r2 = await client.post("/api/v1/events", json=payload, headers=api_key_headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_ingest_batch(client: AsyncClient, api_key_headers: dict):
    response = await client.post(
        "/api/v1/events/batch",
        json={
            "events": [
                {"event_name": "task_created", "user_id": "user_batch_1"},
                {"event_name": "task_completed", "user_id": "user_batch_1"},
            ]
        },
        headers=api_key_headers,
    )
    assert response.status_code == 201
    assert response.json()["created"] == 2


@pytest.mark.asyncio
async def test_ingest_without_api_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/events",
        json={"event_name": "login", "user_id": "user_x"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict, api_key_headers: dict):
    await client.post(
        "/api/v1/events",
        json={"event_name": "logout", "user_id": "user_list_1"},
        headers=api_key_headers,
    )
    response = await client.get("/api/v1/events", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
