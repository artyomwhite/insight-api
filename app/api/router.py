"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import analytics, api_keys, auth, events, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(api_keys.router)
api_router.include_router(events.router)
api_router.include_router(analytics.router)
