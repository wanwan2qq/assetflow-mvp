"""
User profile management endpoints
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth import get_current_user
from app.core.database import get_db_session
from app.core.responses import APIResponse, ErrorCode
from app.models.audit import AuditAction
from app.models.user import RiskLevel, User, UserProfile
from app.services.audit import AuditService
from app.services.profile_asset_service import ProfileAssetService

router = APIRouter()


class UserProfileCreate(BaseModel):
    """User profile creation model"""

    age_range: str
    family_structure: str
    risk_preference: RiskLevel
    monthly_expense: float | None = None


class UserProfileUpdate(BaseModel):
    """User profile update model"""

    # Make all fields optional for partial updates
    age_range: str | None = None
    family_structure: str | None = None
    risk_preference: RiskLevel | None = None
    monthly_expense: float | None = None


class UserProfileResponse(BaseModel):
    """User profile response model"""

    id: int
    user_id: int
    age_range: str
    family_structure: str
    risk_preference: RiskLevel
    monthly_expense: float | None = None


class UserProfileWithAnalysisResponse(UserProfileResponse):
    """User profile response with asset analysis"""

    asset_analysis: dict[str, Any]


@router.post("/", response_model=APIResponse[UserProfileWithAnalysisResponse])
async def create_user_profile(
    profile_data: UserProfileCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserProfileWithAnalysisResponse]:
    """Create user profile with asset analysis"""

    # Check if profile already exists
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        raise HTTPException(
            status_code=400, detail="User profile already exists. Use PUT to update."
        )

    # Create profile with asset analysis
    profile_dict = {
        "age_range": profile_data.age_range,
        "family_structure": profile_data.family_structure,
        "risk_preference": profile_data.risk_preference,
        "monthly_expense": profile_data.monthly_expense,
    }

    profile, analysis = await ProfileAssetService.create_profile_with_assets_analysis(
        db=db,
        user=current_user,
        profile_data=profile_dict,
        user_id_for_audit=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    response_data = UserProfileWithAnalysisResponse(
        **profile.model_dump(), asset_analysis=analysis
    )

    return APIResponse(
        success=True,
        data=response_data,
        message="User profile created successfully with asset analysis",
    )


@router.get("/", response_model=APIResponse[UserProfileWithAnalysisResponse])
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserProfileWithAnalysisResponse]:
    """Get current user's profile with asset analysis"""

    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return APIResponse(
            success=False,
            error_code=ErrorCode.NOT_FOUND,
            message="User profile not found",
        )

    # Get asset analysis
    analysis = await ProfileAssetService.analyze_assets_for_profile(
        db, current_user, profile
    )

    response_data = UserProfileWithAnalysisResponse(
        **profile.model_dump(), asset_analysis=analysis
    )

    return APIResponse(
        success=True,
        data=response_data,
        message="User profile retrieved successfully with asset analysis",
    )


@router.put("/", response_model=APIResponse[UserProfileWithAnalysisResponse])
async def update_user_profile(
    profile_data: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserProfileWithAnalysisResponse]:
    """Update user profile with re-analysis of assets"""

    # Update profile and get new analysis
    update_data = profile_data.model_dump(exclude_unset=True, exclude_none=True)
    # Remove fields that shouldn't be updated
    update_data.pop("id", None)
    update_data.pop("user_id", None)

    if not update_data:
        return APIResponse(
            success=False,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="No valid fields provided for update",
        )

    try:
        profile, analysis = await ProfileAssetService.update_profile_and_reanalyze(
            db=db,
            user=current_user,
            profile_updates=update_data,
            user_id_for_audit=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        response_data = UserProfileWithAnalysisResponse(
            **profile.model_dump(), asset_analysis=analysis
        )

        return APIResponse(
            success=True,
            data=response_data,
            message="User profile updated successfully with updated asset analysis",
        )

    except ValueError as e:
        return APIResponse(
            success=False, error_code=ErrorCode.NOT_FOUND, message=str(e)
        )


@router.delete("/", response_model=APIResponse[dict[str, Any]])
async def delete_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[dict[str, Any]]:
    """Delete user profile"""

    # Get existing profile
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return APIResponse(
            success=False,
            error_code=ErrorCode.NOT_FOUND,
            message="User profile not found",
        )

    # Store old values for audit
    old_values = {
        "age_range": profile.age_range,
        "family_structure": profile.family_structure,
        "risk_preference": profile.risk_preference.value,
        "monthly_expense": profile.monthly_expense,
    }

    profile_id = profile.id
    await db.delete(profile)
    await db.commit()

    # Log audit trail
    await AuditService.log_change(
        db=db,
        table_name="userprofile",
        record_id=profile_id,
        action=AuditAction.DELETE,
        user_id=current_user.id,
        old_values=old_values,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return APIResponse(
        success=True,
        data={"deleted": True},
        message="User profile deleted successfully",
    )
