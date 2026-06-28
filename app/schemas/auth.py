"""Authentication schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["admin@insight.dev"])
    password: str = Field(min_length=8, examples=["changeme123!"])


class TokenResponse(BaseModel):
    access_token: str = Field(
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_in_hours: int = Field(examples=[2])


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
