"""FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.db.session import get_db
from app.models import ApiKey
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.api_key_repo import ApiKeyRepository
from app.repositories.event_repo import EventRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserResponse
from app.services.analytics_service import AnalyticsService
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import AuthService
from app.services.event_service import EventService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_user_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


async def get_api_key_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> ApiKeyRepository:
    return ApiKeyRepository(db)


async def get_event_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> EventRepository:
    return EventRepository(db)


async def get_analytics_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> AnalyticsRepository:
    return AnalyticsRepository(db)


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> AuthService:
    return AuthService(user_repo)


async def get_api_key_service(
    api_key_repo: Annotated[ApiKeyRepository, Depends(get_api_key_repo)],
) -> ApiKeyService:
    return ApiKeyService(api_key_repo)


async def get_event_service(
    event_repo: Annotated[EventRepository, Depends(get_event_repo)],
) -> EventService:
    return EventService(event_repo)


async def get_analytics_service(
    analytics_repo: Annotated[AnalyticsRepository, Depends(get_analytics_repo)],
) -> AnalyticsService:
    return AnalyticsService(analytics_repo)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    if not credentials:
        raise UnauthorizedError("Missing authentication token")
    return await auth_service.get_current_user(credentials.credentials)


async def get_api_key_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key_service: Annotated[ApiKeyService, Depends(get_api_key_service)],
) -> ApiKey:
    if not credentials:
        raise UnauthorizedError("Missing API key")
    return await api_key_service.authenticate(credentials.credentials)


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")
