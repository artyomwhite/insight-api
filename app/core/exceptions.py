"""Custom application exceptions."""

from typing import Any


class AppException(Exception):
    """Base exception for predictable API errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: list | None = None) -> None:
        super().__init__(message, "NOT_FOUND", 404, details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized", details: list | None = None) -> None:
        super().__init__(message, "UNAUTHORIZED", 401, details)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden", details: list | None = None) -> None:
        super().__init__(message, "FORBIDDEN", 403, details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", details: list | None = None) -> None:
        super().__init__(message, "VALIDATION_ERROR", 422, details)


class ConflictError(AppException):
    def __init__(self, message: str = "Conflict", details: list | None = None) -> None:
        super().__init__(message, "CONFLICT", 409, details)
