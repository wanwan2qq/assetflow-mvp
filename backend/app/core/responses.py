"""
Unified API response formats and error codes for AssetFlow
"""

from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standard error codes for API responses"""

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Authentication errors
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Asset management errors
    ASSET_NOT_FOUND = "ASSET_NOT_FOUND"
    ASSET_SAVE_ERROR = "ASSET_SAVE_ERROR"
    INVALID_ASSET_DATA = "INVALID_ASSET_DATA"

    # Search errors
    SEARCH_API_ERROR = "SEARCH_API_ERROR"
    SEARCH_TIMEOUT = "SEARCH_TIMEOUT"
    PROPERTY_NOT_FOUND = "PROPERTY_NOT_FOUND"

    # Chat errors
    CHAT_SESSION_ERROR = "CHAT_SESSION_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"

    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"


class APIResponse(BaseModel, Generic[T]):
    """Standard API response format"""

    success: bool
    data: T | None = None
    error: str | None = None
    error_code: ErrorCode | None = None
    message: str | None = None

    @classmethod
    def success_response(cls, data: T, message: str | None = None) -> "APIResponse[T]":
        """Create a successful response"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(
        cls,
        error: str,
        error_code: ErrorCode,
        message: str | None = None,
    ) -> "APIResponse[None]":
        """Create an error response"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            message=message,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response format"""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class HealthResponse(BaseModel):
    """Health check response format"""

    status: str
    service: str | None = None
    database: str | None = None
    timestamp: str | None = None
    version: str | None = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""

    field: str
    message: str
    value: Any | None = None


class ValidationErrorResponse(BaseModel):
    """Validation error response format"""

    success: bool = False
    error: str = "Validation failed"
    error_code: ErrorCode = ErrorCode.VALIDATION_ERROR
    details: list[ValidationErrorDetail]


def create_error_response(
    error: str,
    error_code: ErrorCode,
    message: str | None = None,
) -> APIResponse[None]:
    """Create an error response (convenience function)"""
    return APIResponse.error_response(
        error=error, error_code=error_code, message=message
    )
