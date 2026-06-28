"""API key management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_api_key_service, get_current_user
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ApiKeyRotateResponse,
)
from app.schemas.auth import UserResponse
from app.schemas.common import MessageResponse
from app.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.get(
    "",
    response_model=list[ApiKeyResponse],
    summary="List API keys",
    description="Returns all API keys. The full key value is never included.",
    responses={200: {"description": "List of API keys"}, 401: {"description": "Unauthorized"}},
)
async def list_api_keys(
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
) -> list[ApiKeyResponse]:
    return await service.list_keys()


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description=(
        "Generate a new API key for event ingestion. "
        "The full key is returned **only once** — store it securely."
    ),
    responses={
        201: {"description": "API key created"},
        401: {"description": "Unauthorized"},
    },
)
async def create_api_key(
    body: ApiKeyCreate,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
) -> ApiKeyCreatedResponse:
    return await service.create_key(body.name)


@router.post(
    "/{key_id}/rotate",
    response_model=ApiKeyRotateResponse,
    summary="Rotate API key",
    description=(
        "Generate a new key value for an existing API key record. "
        "The new key is returned **only once**."
    ),
    responses={
        200: {"description": "Key rotated"},
        404: {"description": "API key not found"},
        401: {"description": "Unauthorized"},
    },
)
async def rotate_api_key(
    key_id: UUID,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
) -> ApiKeyRotateResponse:
    return await service.rotate_key(key_id)


@router.delete(
    "/{key_id}",
    response_model=MessageResponse,
    summary="Delete API key",
    description="Permanently revoke and delete an API key.",
    responses={
        200: {"description": "Key deleted"},
        404: {"description": "API key not found"},
        401: {"description": "Unauthorized"},
    },
)
async def delete_api_key(
    key_id: UUID,
    _: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
) -> MessageResponse:
    await service.delete_key(key_id)
    return MessageResponse(message="API key deleted successfully")
