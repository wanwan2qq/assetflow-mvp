"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.services.auth import auth_service
from app.services.sms_service import sms_service

router = APIRouter()


# Request/Response models
class SendSMSRequest(BaseModel):
    """Send SMS verification code request"""

    phone: str = Field(..., min_length=11, max_length=15, description="手机号")


class SMSResponse(BaseModel):
    """SMS sending response"""

    success: bool
    message: str
    code: str


class PhoneLoginRequest(BaseModel):
    """Phone login request"""

    phone: str = Field(..., min_length=11, max_length=15, description="手机号")
    verification_code: str = Field(
        ..., min_length=4, max_length=6, description="验证码"
    )


class DeviceLoginRequest(BaseModel):
    """Device ID login request"""

    device_id: str = Field(..., min_length=1, max_length=255, description="设备ID")


class BindPhoneRequest(BaseModel):
    """Bind phone to user request"""

    phone: str = Field(..., min_length=11, max_length=15, description="手机号")
    verification_code: str = Field(
        ..., min_length=4, max_length=6, description="验证码"
    )


class AuthResponse(BaseModel):
    """Authentication response"""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    phone: str
    device_id: str | None = None


class UserResponse(BaseModel):
    """User information response"""

    id: int
    phone: str
    device_id: str | None = None
    created_at: str


@router.post("/send-sms", response_model=SMSResponse)
async def send_sms_verification_code(request: SendSMSRequest):
    """
    Send SMS verification code to phone number
    Rate limited to prevent abuse
    """
    result = await sms_service.request_verification_code(request.phone)
    
    if not result["success"]:
        if result["code"] == "RATE_LIMITED":
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=result["message"],
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )
    
    return SMSResponse(**result)


@router.post("/login/phone", response_model=AuthResponse)
async def login_with_phone(
    request: PhoneLoginRequest, session: AsyncSession = Depends(get_db_session)
):
    """
    Login with phone number and SMS verification code
    Creates new user if phone number doesn't exist
    """
    # Verify SMS code
    is_valid = await sms_service.verify_code(request.phone, request.verification_code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Try to find existing user
    user = await auth_service.authenticate_user_by_phone(session, request.phone)

    # Create new user if doesn't exist
    if not user:
        user = await auth_service.create_user_by_phone(session, request.phone)

    # Generate access token
    access_token = auth_service.create_access_token(user.id)

    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        phone=user.phone,
        device_id=user.device_id,
    )


@router.post("/login/device", response_model=AuthResponse)
async def login_with_device(
    request: DeviceLoginRequest, session: AsyncSession = Depends(get_db_session)
):
    """
    Anonymous login with device ID
    Creates new user if device ID doesn't exist
    """
    # Try to find existing user
    user = await auth_service.authenticate_user_by_device(session, request.device_id)

    # Create new anonymous user if doesn't exist
    if not user:
        user = await auth_service.create_user_by_device(session, request.device_id)

    # Generate access token
    access_token = auth_service.create_access_token(user.id)

    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        phone=user.phone,
        device_id=user.device_id,
    )


@router.post("/bind-phone", response_model=AuthResponse)
async def bind_phone_to_user(
    request: BindPhoneRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Bind phone number to current anonymous user
    Requires valid authentication token
    """
    # Verify SMS code
    is_valid = await sms_service.verify_code(request.phone, request.verification_code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Bind phone to current user
    updated_user = await auth_service.bind_phone_to_user(
        session, current_user.id, request.phone
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already in use by another user",
        )

    # Generate new access token
    access_token = auth_service.create_access_token(updated_user.id)

    return AuthResponse(
        access_token=access_token,
        user_id=updated_user.id,
        phone=updated_user.phone,
        device_id=updated_user.device_id,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    Requires valid authentication token
    """
    return UserResponse(
        id=current_user.id,
        phone=current_user.phone,
        device_id=current_user.device_id,
        created_at=current_user.created_at.isoformat(),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh access token
    Requires valid authentication token
    """
    # Generate new access token
    access_token = auth_service.create_access_token(current_user.id)

    return AuthResponse(
        access_token=access_token,
        user_id=current_user.id,
        phone=current_user.phone,
        device_id=current_user.device_id,
    )
