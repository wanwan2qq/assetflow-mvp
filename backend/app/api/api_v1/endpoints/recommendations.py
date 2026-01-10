"""
Recommendation API endpoints for commercial products
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.models.commercial import CommercialProduct
from app.models.user import User
from app.services.recommendation_service import get_recommendation_service

logger = logging.getLogger(__name__)
router = APIRouter()


class RecommendationRequest(BaseModel):
    """Request model for getting recommendations"""

    risk_warnings: list[dict[str, Any]]
    user_profile_data: dict[str, Any] | None = None


class InteractionTrackingRequest(BaseModel):
    """Request model for tracking user interactions"""

    product_id: int
    interaction_type: str  # "view", "click", "contact", "dismiss"
    metadata: dict[str, Any] | None = None
    session_id: str | None = None


@router.get("/products/{category}")
async def get_products_by_category(
    category: str,
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Get commercial products by category"""
    try:
        recommendation_service = get_recommendation_service()

        # Get user profile if available
        user_profile = getattr(current_user, "profile", None)

        products = await recommendation_service.get_recommendations_by_category(
            category=category, user_profile=user_profile, limit=limit
        )

        # Convert to response format
        return [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "provider": product.provider,
                "contact_info": product.contact_info,
                "priority": product.priority,
                "category": product.category,
            }
            for product in products
        ]

    except Exception as e:
        logger.error(f"Error getting products by category: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get recommendations"
        ) from e


@router.post("/recommendations")
async def get_recommendations_for_risks(
    request: RecommendationRequest, current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """Get product recommendations based on risk warnings"""
    try:
        recommendation_service = get_recommendation_service()

        # Get user profile if available
        user_profile = getattr(current_user, "profile", None)

        recommendations = await recommendation_service.get_recommendations_for_risks(
            risk_warnings=request.risk_warnings, user_profile=user_profile, limit=10
        )

        return recommendations

    except Exception as e:
        logger.error(f"Error getting recommendations for risks: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get recommendations"
        ) from e


@router.post("/action-cards")
async def generate_action_cards(
    portfolio_analysis: dict[str, Any], current_user: User = Depends(get_current_user)
) -> list[str]:
    """Generate action cards based on portfolio analysis"""
    try:
        recommendation_service = get_recommendation_service()

        # Get user profile if available
        user_profile = getattr(current_user, "profile", None)

        action_cards = await recommendation_service.generate_action_cards_for_portfolio(
            portfolio_analysis=portfolio_analysis, user_profile=user_profile
        )

        return action_cards

    except Exception as e:
        logger.error(f"Error generating action cards: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate action cards"
        ) from e


@router.post("/interactions")
async def track_user_interaction(
    request: InteractionTrackingRequest, current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Track user interaction with recommended products"""
    try:
        recommendation_service = get_recommendation_service()

        await recommendation_service.track_user_interaction(
            user_id=current_user.id,
            product_id=request.product_id,
            interaction_type=request.interaction_type,
            metadata=request.metadata,
            session_id=request.session_id,
        )

        return {"message": "Interaction tracked successfully"}

    except Exception as e:
        logger.error(f"Error tracking user interaction: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to track interaction"
        ) from e


@router.get("/categories")
async def get_available_categories(
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Get list of available product categories"""
    try:
        from sqlmodel import select

        from app.core.database import get_db_session

        async with get_db_session() as session:
            # Get distinct categories from active products
            statement = (
                select(CommercialProduct.category)
                .where(CommercialProduct.is_active)
                .distinct()
            )

            result = await session.execute(statement)
            categories = result.scalars().all()

            return list(categories)

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories") from e


@router.get("/products/{product_id}")
async def get_product_details(
    product_id: int, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get detailed information about a specific product"""
    try:
        from sqlmodel import select

        from app.core.database import get_db_session

        async with get_db_session() as session:
            statement = select(CommercialProduct).where(
                CommercialProduct.id == product_id, CommercialProduct.is_active
            )

            result = await session.execute(statement)
            product = result.scalar_one_or_none()

            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            return {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "provider": product.provider,
                "contact_info": product.contact_info,
                "priority": product.priority,
                "category": product.category,
                "target_tags": product.target_tags,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get product details"
        ) from e
