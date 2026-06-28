"""API key management business logic."""

from uuid import UUID

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import generate_api_key, verify_api_key
from app.models import ApiKey
from app.repositories.api_key_repo import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreatedResponse, ApiKeyResponse, ApiKeyRotateResponse


class ApiKeyService:
    def __init__(self, api_key_repo: ApiKeyRepository) -> None:
        self.api_key_repo = api_key_repo

    async def list_keys(self) -> list[ApiKeyResponse]:
        keys = await self.api_key_repo.list_all()
        return [ApiKeyResponse.model_validate(k) for k in keys]

    async def create_key(self, name: str) -> ApiKeyCreatedResponse:
        full_key, prefix, key_hash = generate_api_key()
        api_key = await self.api_key_repo.create(name=name, key_prefix=prefix, key_hash=key_hash)
        return ApiKeyCreatedResponse(
            **ApiKeyResponse.model_validate(api_key).model_dump(),
            key=full_key,
        )

    async def rotate_key(self, key_id: UUID) -> ApiKeyRotateResponse:
        api_key = await self._get_or_404(key_id)
        full_key, prefix, key_hash = generate_api_key()
        api_key.key_prefix = prefix
        api_key.key_hash = key_hash
        api_key.is_active = True
        await self.api_key_repo.update(api_key)
        return ApiKeyRotateResponse(
            **ApiKeyResponse.model_validate(api_key).model_dump(),
            key=full_key,
        )

    async def delete_key(self, key_id: UUID) -> None:
        api_key = await self._get_or_404(key_id)
        await self.api_key_repo.delete(api_key)

    async def authenticate(self, raw_key: str) -> ApiKey:
        if len(raw_key) < 12:
            raise UnauthorizedError("Invalid API key")
        prefix = raw_key[:12]
        api_key = await self.api_key_repo.get_by_prefix(prefix)
        if not api_key or not verify_api_key(raw_key, api_key.key_hash):
            raise UnauthorizedError("Invalid API key")
        await self.api_key_repo.touch_last_used(api_key)
        return api_key

    async def _get_or_404(self, key_id: UUID) -> ApiKey:
        api_key = await self.api_key_repo.get_by_id(key_id)
        if not api_key:
            raise NotFoundError("API key not found")
        return api_key
