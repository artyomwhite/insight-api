"""API key data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey


class ApiKeyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> list[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, key_id: UUID) -> ApiKey | None:
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == key_id))
        return result.scalar_one_or_none()

    async def get_by_prefix(self, prefix: str) -> ApiKey | None:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, key_prefix: str, key_hash: str) -> ApiKey:
        api_key = ApiKey(name=name, key_prefix=key_prefix, key_hash=key_hash)
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def update(self, api_key: ApiKey) -> ApiKey:
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key

    async def delete(self, api_key: ApiKey) -> None:
        await self.db.delete(api_key)

    async def touch_last_used(self, api_key: ApiKey) -> None:
        api_key.last_used_at = datetime.now(UTC)
        await self.db.flush()
