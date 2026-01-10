"""
Comprehensive error handling and user experience optimization
"""

import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorCode:
    """Standardized error codes for the application"""

    # Authentication errors
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"

    # Asset management errors
    ASSET_NOT_FOUND = "ASSET_NOT_FOUND"
    ASSET_INVALID_TYPE = "ASSET_INVALID_TYPE"
    ASSET_INVALID_VALUE = "ASSET_INVALID_VALUE"
    ASSET_CREATION_FAILED = "ASSET_CREATION_FAILED"
    ASSET_UPDATE_FAILED = "ASSET_UPDATE_FAILED"
    ASSET_DELETE_FAILED = "ASSET_DELETE_FAILED"

    # User management errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_PROFILE_INVALID = "USER_PROFILE_INVALID"

    # AI and search errors
    AI_SERVICE_UNAVAILABLE = "AI_SERVICE_UNAVAILABLE"
    SEARCH_SERVICE_TIMEOUT = "SEARCH_SERVICE_TIMEOUT"
    SEARCH_NO_RESULTS = "SEARCH_NO_RESULTS"
    AI_RESPONSE_INVALID = "AI_RESPONSE_INVALID"

    # Database errors
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_CONSTRAINT_VIOLATION = "DATABASE_CONSTRAINT_VIOLATION"
    DATABASE_TRANSACTION_FAILED = "DATABASE_TRANSACTION_FAILED"

    # WebSocket errors
    WEBSOCKET_CONNECTION_FAILED = "WEBSOCKET_CONNECTION_FAILED"
    WEBSOCKET_AUTH_FAILED = "WEBSOCKET_AUTH_FAILED"
    WEBSOCKET_MESSAGE_INVALID = "WEBSOCKET_MESSAGE_INVALID"

    # General errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class AssetFlowException(Exception):
    """Base exception class for AssetFlow application"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AssetFlowException):
    """Authentication related errors"""

    def __init__(self, message: str, error_code: str = ErrorCode.AUTH_INVALID_TOKEN):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(AssetFlowException):
    """Authorization related errors"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(AssetFlowException):
    """Data validation errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ResourceNotFoundError(AssetFlowException):
    """Resource not found errors"""

    def __init__(self, resource_type: str, resource_id: str | int):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ServiceUnavailableError(AssetFlowException):
    """External service unavailable errors"""

    def __init__(self, service_name: str, message: str = None):
        default_message = f"{service_name} service is currently unavailable"
        super().__init__(
            message=message or default_message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service_name},
        )


class DatabaseError(AssetFlowException):
    """Database related errors"""

    def __init__(self, message: str, original_error: Exception | None = None):
        error_code = ErrorCode.DATABASE_CONNECTION_ERROR

        if isinstance(original_error, IntegrityError):
            error_code = ErrorCode.DATABASE_CONSTRAINT_VIOLATION

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"original_error": str(original_error) if original_error else None},
        )


def create_error_response(
    message: str,
    error_code: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Create standardized error response"""

    error_response = {
        "success": False,
        "error": {
            "message": message,
            "code": error_code,
            "details": details or {},
        },
        "timestamp": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
    }

    if request_id:
        error_response["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=error_response)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except AssetFlowException as e:
            logger.warning(
                f"AssetFlow exception: {e.error_code} - {e.message}",
                extra={
                    "error_code": e.error_code,
                    "status_code": e.status_code,
                    "details": e.details,
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            return create_error_response(
                message=e.message,
                error_code=e.error_code,
                status_code=e.status_code,
                details=e.details,
                request_id=getattr(request.state, "request_id", None),
            )

        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions normally
            raise e

        except SQLAlchemyError as e:
            logger.error(
                f"Database error: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                },
            )

            return create_error_response(
                message="Database operation failed",
                error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=getattr(request.state, "request_id", None),
            )

        except Exception as e:
            # Log unexpected errors with full traceback
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

            # Don't expose internal error details in production
            return create_error_response(
                message="An unexpected error occurred",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                request_id=getattr(request.state, "request_id", None),
            )


class GracefulDegradationHandler:
    """Handle service degradation gracefully"""

    @staticmethod
    def handle_search_service_failure(
        city: str, community: str, area: float
    ) -> dict[str, Any]:
        """Handle search service failure with fallback"""
        logger.warning(f"Search service failed for {city} {community}, using fallback")

        # Provide fallback estimation based on city
        fallback_prices = {
            "北京": 60000,
            "上海": 55000,
            "深圳": 50000,
            "广州": 35000,
            "杭州": 30000,
            "南京": 25000,
        }

        base_price = fallback_prices.get(city, 20000)
        estimated_value = base_price * area * 0.9  # Conservative estimate

        return {
            "estimated_price": estimated_value,
            "price_per_sqm": base_price,
            "source": "fallback_estimation",
            "confidence": 0.3,
            "message": "搜索服务暂时不可用，使用保守估算",
            "requires_manual_confirmation": True,
        }

    @staticmethod
    def handle_ai_service_failure(user_message: str) -> str:
        """Handle AI service failure with fallback response"""
        logger.warning("AI service failed, using fallback response")

        # Provide helpful fallback based on message content
        if any(keyword in user_message.lower() for keyword in ["房产", "房子", "房屋"]):
            return """抱歉，AI服务暂时不可用。请您直接提供以下房产信息：
1. 房产位置（城市和小区）
2. 房产面积
3. 大概的市场价值

我会帮您记录并分析资产配置。"""

        elif any(
            keyword in user_message.lower() for keyword in ["现金", "存款", "银行"]
        ):
            return """抱歉，AI服务暂时不可用。请您直接告诉我：
1. 现金和存款总额
2. 是否有其他投资（股票、基金等）
3. 是否有负债（房贷、信用卡等）

我会帮您分析资产配置。"""

        else:
            return """抱歉，AI服务暂时不可用。您可以：
1. 直接在资产管理页面添加您的资产信息
2. 稍后重试对话功能
3. 联系客服获得人工协助

感谢您的理解！"""

    @staticmethod
    def handle_database_failure() -> dict[str, Any]:
        """Handle database failure with cached data if available"""
        logger.error("Database service failed")

        return {
            "success": False,
            "error": {
                "message": "数据服务暂时不可用，请稍后重试",
                "code": ErrorCode.DATABASE_CONNECTION_ERROR,
                "details": {
                    "fallback_available": False,
                    "retry_after": 30,
                },
            },
        }


class UserExperienceOptimizer:
    """Optimize user experience during errors and edge cases"""

    @staticmethod
    def get_user_friendly_message(
        error_code: str, context: dict | None = None
    ) -> str:
        """Convert technical error codes to user-friendly messages"""

        messages = {
            ErrorCode.AUTH_INVALID_TOKEN: "登录已过期，请重新登录",
            ErrorCode.AUTH_INVALID_CREDENTIALS: "手机号或验证码错误，请检查后重试",
            ErrorCode.ASSET_NOT_FOUND: "找不到指定的资产信息",
            ErrorCode.ASSET_INVALID_VALUE: "资产价值必须为正数",
            ErrorCode.DATABASE_CONNECTION_ERROR: "数据服务暂时不可用，请稍后重试",
            ErrorCode.AI_SERVICE_UNAVAILABLE: "AI服务暂时不可用，您可以手动输入资产信息",
            ErrorCode.SEARCH_SERVICE_TIMEOUT: "房产搜索超时，请手动输入估值或稍后重试",
            ErrorCode.WEBSOCKET_CONNECTION_FAILED: "连接中断，正在尝试重新连接...",
            ErrorCode.VALIDATION_ERROR: "输入信息有误，请检查后重试",
            ErrorCode.RATE_LIMIT_EXCEEDED: "操作过于频繁，请稍后重试",
        }

        return messages.get(error_code, "系统暂时不可用，请稍后重试")

    @staticmethod
    def get_recovery_suggestions(error_code: str) -> list[str]:
        """Provide recovery suggestions for different error types"""

        suggestions = {
            ErrorCode.AUTH_INVALID_TOKEN: [
                "点击重新登录",
                "检查网络连接",
                "清除应用缓存后重试",
            ],
            ErrorCode.ASSET_INVALID_VALUE: [
                "确保输入的金额为正数",
                "检查数字格式是否正确",
                "如有疑问可联系客服",
            ],
            ErrorCode.SEARCH_SERVICE_TIMEOUT: [
                "手动输入房产估值",
                "稍后重试搜索功能",
                "联系客服获取帮助",
            ],
            ErrorCode.AI_SERVICE_UNAVAILABLE: [
                "使用资产管理页面手动添加",
                "稍后重试对话功能",
                "查看帮助文档",
            ],
            ErrorCode.DATABASE_CONNECTION_ERROR: [
                "检查网络连接",
                "稍后重试",
                "联系技术支持",
            ],
        }

        return suggestions.get(error_code, ["稍后重试", "联系客服获取帮助"])

    @staticmethod
    def should_retry_automatically(error_code: str) -> bool:
        """Determine if an error should trigger automatic retry"""

        auto_retry_errors = {
            ErrorCode.DATABASE_CONNECTION_ERROR,
            ErrorCode.SEARCH_SERVICE_TIMEOUT,
            ErrorCode.WEBSOCKET_CONNECTION_FAILED,
        }

        return error_code in auto_retry_errors

    @staticmethod
    def get_retry_delay(error_code: str, attempt: int) -> int:
        """Get retry delay in seconds with exponential backoff"""

        base_delays = {
            ErrorCode.DATABASE_CONNECTION_ERROR: 2,
            ErrorCode.SEARCH_SERVICE_TIMEOUT: 5,
            ErrorCode.WEBSOCKET_CONNECTION_FAILED: 1,
        }

        base_delay = base_delays.get(error_code, 5)
        return min(base_delay * (2**attempt), 60)  # Max 60 seconds


# Utility functions for common error scenarios
def handle_asset_not_found(asset_id: int, user_id: int) -> AssetFlowException:
    """Handle asset not found scenario"""
    return ResourceNotFoundError("asset", asset_id)


def handle_user_not_found(user_id: int) -> AssetFlowException:
    """Handle user not found scenario"""
    return ResourceNotFoundError("user", user_id)


def handle_validation_error(
    field: str, value: Any, expected: str
) -> AssetFlowException:
    """Handle validation error scenario"""
    return ValidationError(
        message=f"Invalid value for {field}",
        details={
            "field": field,
            "value": str(value),
            "expected": expected,
        },
    )


def handle_database_constraint_violation(
    constraint: str, details: dict[str, Any]
) -> AssetFlowException:
    """Handle database constraint violation"""
    return DatabaseError(
        message=f"Database constraint violation: {constraint}", original_error=None
    )
