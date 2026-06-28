"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Liveness check",
    description="Returns service status. Used by load balancers and orchestrators.",
    responses={200: {"description": "Service is alive"}},
)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness check",
    description="Verifies database connectivity before accepting traffic.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Database unavailable"},
    },
)
async def readiness(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
