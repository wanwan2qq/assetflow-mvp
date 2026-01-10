"""
Assets API endpoints
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.auth import get_current_user, verify_user_access
from app.core.database import get_db_session
from app.core.responses import APIResponse, ErrorCode
from app.models.audit import AuditAction
from app.models.user import AssetType, User, UserAsset, UserProfile
from app.services.audit import AuditService
from app.services.portfolio_analyzer import PortfolioAnalyzer

router = APIRouter()


# Request/Response models
class AssetCreateRequest(BaseModel):
    """Asset creation request"""

    asset_type: AssetType
    name: str = Field(..., min_length=1, max_length=200)
    value: float = Field(..., gt=0)
    is_confirmed: bool = False
    extra_data: dict | None = None


class AssetUpdateRequest(BaseModel):
    """Asset update request"""

    asset_type: AssetType | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    value: float | None = Field(None, gt=0)
    is_confirmed: bool | None = None
    extra_data: dict | None = None


class AssetResponse(BaseModel):
    """Asset response"""

    id: int
    user_id: int
    asset_type: AssetType
    name: str
    value: float
    is_confirmed: bool
    extra_data: dict | None = None
    created_at: str
    updated_at: str


class PortfolioHealthResponse(BaseModel):
    """Portfolio health analysis response with Standard & Poor's Four Quadrant Model"""

    net_worth: float
    real_estate_ratio: float
    liquidity_ratio: float
    risk_warnings: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    overall_risk_level: str
    analysis_summary: str

    # Standard & Poor's Four Quadrant Analysis
    quadrant_analysis: dict[str, Any]
    quadrant_allocations: dict[str, float]
    ideal_allocations: dict[str, float]
    allocation_gaps: dict[str, float]


@router.get("/{user_id}", response_model=APIResponse[list[AssetResponse]])
async def get_user_assets(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[list[AssetResponse]]:
    """
    Get all assets for a specific user
    Requires authentication and user can only access their own assets
    """
    # Verify user can access this data
    verify_user_access(current_user, user_id)

    # Query user assets
    stmt = select(UserAsset).where(UserAsset.user_id == user_id)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    asset_responses = [
        AssetResponse(
            id=asset.id,
            user_id=asset.user_id,
            asset_type=asset.asset_type,
            name=asset.name,
            value=asset.value,
            is_confirmed=asset.is_confirmed,
            extra_data=asset.extra_data,
            created_at=asset.created_at.isoformat(),
            updated_at=asset.updated_at.isoformat(),
        )
        for asset in assets
    ]

    return APIResponse(
        success=True,
        data=asset_responses,
        message=f"Retrieved {len(asset_responses)} assets",
    )


@router.post("/{user_id}", response_model=APIResponse[AssetResponse])
async def create_user_asset(
    user_id: int,
    asset_request: AssetCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[AssetResponse]:
    """
    Create a new asset for a specific user
    Requires authentication and user can only create assets for themselves
    """
    # Verify user can access this data
    verify_user_access(current_user, user_id)

    # Create new asset
    asset = UserAsset(
        user_id=user_id,
        asset_type=asset_request.asset_type,
        name=asset_request.name,
        value=asset_request.value,
        is_confirmed=asset_request.is_confirmed,
        extra_data=asset_request.extra_data,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    # Log audit trail with asset history
    await AuditService.log_asset_change(
        db=db,
        asset=asset,
        action=AuditAction.CREATE,
        user_id=current_user.id,
        new_values={
            "asset_type": asset.asset_type.value,
            "name": asset.name,
            "value": asset.value,
            "is_confirmed": asset.is_confirmed,
            "extra_data": asset.extra_data,
        },
        change_reason="Asset created by user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    asset_response = AssetResponse(
        id=asset.id,
        user_id=asset.user_id,
        asset_type=asset.asset_type,
        name=asset.name,
        value=asset.value,
        is_confirmed=asset.is_confirmed,
        extra_data=asset.extra_data,
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat(),
    )

    return APIResponse(
        success=True, data=asset_response, message="Asset created successfully"
    )


@router.put("/{user_id}/{asset_id}", response_model=APIResponse[AssetResponse])
async def update_user_asset(
    user_id: int,
    asset_id: int,
    asset_request: AssetUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[AssetResponse]:
    """
    Update a specific asset
    Requires authentication and user can only update their own assets
    """
    # Verify user can access this data
    verify_user_access(current_user, user_id)

    # Find asset
    stmt = select(UserAsset).where(
        UserAsset.id == asset_id, UserAsset.user_id == user_id
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        return APIResponse(
            success=False, error_code=ErrorCode.NOT_FOUND, message="Asset not found"
        )

    # Store old values for audit
    old_values = {
        "asset_type": asset.asset_type.value,
        "name": asset.name,
        "value": asset.value,
        "is_confirmed": asset.is_confirmed,
        "extra_data": asset.extra_data,
    }

    # Update fields that are provided
    update_data = asset_request.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if hasattr(asset, field):
            setattr(asset, field, value)

    # Update timestamp
    asset.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(asset)

    # Store new values for audit
    new_values = {
        "asset_type": asset.asset_type.value,
        "name": asset.name,
        "value": asset.value,
        "is_confirmed": asset.is_confirmed,
        "extra_data": asset.extra_data,
    }

    # Log audit trail with asset history
    await AuditService.log_asset_change(
        db=db,
        asset=asset,
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        old_values=old_values,
        new_values=new_values,
        change_reason="Asset updated by user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    asset_response = AssetResponse(
        id=asset.id,
        user_id=asset.user_id,
        asset_type=asset.asset_type,
        name=asset.name,
        value=asset.value,
        is_confirmed=asset.is_confirmed,
        extra_data=asset.extra_data,
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat(),
    )

    return APIResponse(
        success=True, data=asset_response, message="Asset updated successfully"
    )


@router.delete("/{user_id}/{asset_id}", response_model=APIResponse[dict[str, Any]])
async def delete_user_asset(
    user_id: int,
    asset_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[dict[str, Any]]:
    """
    Delete a specific asset
    Requires authentication and user can only delete their own assets
    """
    # Verify user can access this data
    verify_user_access(current_user, user_id)

    # Find asset
    stmt = select(UserAsset).where(
        UserAsset.id == asset_id, UserAsset.user_id == user_id
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        return APIResponse(
            success=False, error_code=ErrorCode.NOT_FOUND, message="Asset not found"
        )

    # Store old values for audit
    old_values = {
        "asset_type": asset.asset_type.value,
        "name": asset.name,
        "value": asset.value,
        "is_confirmed": asset.is_confirmed,
        "extra_data": asset.extra_data,
    }

    # Log audit trail before deletion
    await AuditService.log_change(
        db=db,
        table_name="userasset",
        record_id=asset.id,
        action=AuditAction.DELETE,
        user_id=current_user.id,
        old_values=old_values,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        extra_metadata={"change_reason": "Asset deleted by user"},
    )

    await db.delete(asset)
    await db.commit()

    return APIResponse(
        success=True, data={"deleted": True}, message="Asset deleted successfully"
    )


@router.get(
    "/{user_id}/portfolio/health", response_model=APIResponse[PortfolioHealthResponse]
)
async def get_portfolio_health(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[PortfolioHealthResponse]:
    """
    Get portfolio health analysis for a specific user
    Requires authentication and user can only access their own portfolio analysis
    """
    # Verify user can access this data
    verify_user_access(current_user, user_id)

    # Get user assets
    assets_stmt = select(UserAsset).where(UserAsset.user_id == user_id)
    assets_result = await db.execute(assets_stmt)
    assets = list(assets_result.scalars().all())

    # Get user profile
    profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    profile_result = await db.execute(profile_stmt)
    user_profile = profile_result.scalar_one_or_none()

    # Perform portfolio analysis
    analyzer = PortfolioAnalyzer()
    analysis = analyzer.analyze_portfolio(assets, user_profile)
    summary = analyzer.generate_analysis_summary(analysis)

    portfolio_response = PortfolioHealthResponse(
        net_worth=analysis.net_worth,
        real_estate_ratio=analysis.real_estate_ratio,
        liquidity_ratio=analysis.liquidity_ratio,
        risk_warnings=analysis.risk_warnings,
        recommendations=analysis.recommendations,
        overall_risk_level=analysis.overall_risk_level.value,
        analysis_summary=summary,
        # Standard & Poor's Four Quadrant Analysis
        quadrant_analysis=analysis.quadrant_analysis,
        quadrant_allocations={
            k.value: v for k, v in analysis.quadrant_allocations.items()
        },
        ideal_allocations={k.value: v for k, v in analysis.ideal_allocations.items()},
        allocation_gaps={k.value: v for k, v in analysis.allocation_gaps.items()},
    )

    return APIResponse(
        success=True,
        data=portfolio_response,
        message="Portfolio health analysis completed",
    )
