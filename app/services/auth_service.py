"""Authentication business logic."""

from jose import JWTError

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenResponse, UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")

        settings = get_settings()
        token = create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            expires_in_hours=settings.access_token_expire_hours,
        )

    async def get_current_user(self, token: str) -> UserResponse:
        from app.core.security import decode_access_token

        try:
            payload = decode_access_token(token)
            if payload.get("type") != "access":
                raise UnauthorizedError("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedError("Invalid token")
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc

        from uuid import UUID

        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return UserResponse.model_validate(user)
