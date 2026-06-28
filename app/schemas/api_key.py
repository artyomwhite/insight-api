"""API key schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Production SDK"])


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only once on creation or rotation."""

    key: str = Field(
        description="Full API key — store securely, shown only once",
        examples=["ins_abc123xyz..."],
    )


class ApiKeyRotateResponse(ApiKeyCreatedResponse):
    message: str = Field(default="API key rotated successfully")
