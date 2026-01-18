"""
Commercial Recommendation Service for AssetFlow

This service handles the matching and ranking of commercial products
based on user portfolio analysis and risk warnings.
"""

import logging
from typing import Any

from sqlmodel import Session, select

from app.core.database import get_db_session
from app.models.commercial import CommercialProduct
from app.models.user import UserProfile
from app.services.ui_component_service import get_ui_component_service

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating commercial product recommendations"""

    def __init__(self):
        self.ui_service = get_ui_component_service()

    async def get_recommendations_for_risks(
        self,
        risk_warnings: list[dict[str, Any]],
        user_profile: UserProfile | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get commercial product recommendations based on risk warnings"""
        recommendations = []

        try:
            async with get_db_session() as session:
                for warning in risk_warnings:
                    risk_type = warning.get("type", "")
                    category = self._map_risk_to_category(risk_type)

                    if category:
                        products = await self._query_products_by_category(
                            session, category, user_profile, limit=2
                        )

                        for product in products:
                            recommendation = self._create_recommendation_from_product(
                                product, warning
                            )
                            recommendations.append(recommendation)

                # Sort by priority and limit results
                recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
                return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error getting recommendations for risks: {e}")
            return []

    async def get_recommendations_by_category(
        self, category: str, user_profile: UserProfile | None = None, limit: int = 3
    ) -> list[CommercialProduct]:
        """Get commercial products by category with user-specific filtering"""
        try:
            async with get_db_session() as session:
                return await self._query_products_by_category(
                    session, category, user_profile, limit
                )
        except Exception as e:
            logger.error(f"Error getting recommendations by category: {e}")
            return []

    async def generate_action_cards_for_portfolio(
        self,
        portfolio_analysis: dict[str, Any],
        user_profile: UserProfile | None = None,
    ) -> list[str]:
        """Generate action cards based on portfolio analysis"""
        action_cards = []

        try:
            risk_warnings = portfolio_analysis.get("risk_warnings", [])

            # Get commercial products for each risk
            async with get_db_session() as session:
                for warning in risk_warnings:
                    risk_type = warning.get("type", "")
                    category = self._map_risk_to_category(risk_type)

                    if category:
                        products = await self._query_products_by_category(
                            session, category, user_profile, limit=1
                        )

                        if products:
                            product = products[0]
                            card = self.ui_service.generate_action_card(
                                action_type=risk_type,
                                title=warning.get("title", "风险提醒"),
                                description=f"{warning.get('recommendation', '')}\n\n推荐服务商: {product.provider}",
                                priority=self._map_severity_to_priority(
                                    warning.get("severity", "medium")
                                ),
                                contact_info=product.contact_info,
                            )
                            action_cards.append(card)
                        else:
                            # Generate generic action card without commercial product
                            card = self.ui_service.generate_action_card(
                                action_type=risk_type,
                                title=warning.get("title", "风险提醒"),
                                description=warning.get("recommendation", ""),
                                priority=self._map_severity_to_priority(
                                    warning.get("severity", "medium")
                                ),
                            )
                            action_cards.append(card)

        except Exception as e:
            logger.error(f"Error generating action cards for portfolio: {e}")

        return action_cards

    async def _query_products_by_category(
        self,
        session: Session,
        category: str,
        user_profile: UserProfile | None = None,
        limit: int = 3,
    ) -> list[CommercialProduct]:
        """Query commercial products by category with filtering and ranking"""
        try:
            # Base query for active products in category
            statement = (
                select(CommercialProduct)
                .where(CommercialProduct.category == category)
                .where(CommercialProduct.is_active)
                .order_by(CommercialProduct.priority.desc())
                .limit(limit)
            )

            # Apply user profile filtering if available
            if user_profile:
                # Filter by target tags based on user profile
                user_tags = self._extract_user_tags(user_profile)
                if user_tags:
                    # In a real implementation, you'd use array operations
                    # For now, we'll filter in Python after the query
                    pass

            result = await session.execute(statement)
            products = result.scalars().all()

            # Apply user profile filtering in Python if needed
            if user_profile and products:
                products = self._filter_products_by_user_profile(products, user_profile)

            return products

        except Exception as e:
            logger.error(f"Error querying products by category: {e}")
            return []

    def _map_risk_to_category(self, risk_type: str) -> str | None:
        """
        Map risk type to commercial product category
        
        Updated to support Standard & Poor's 4-Quadrant Model risk types:
        - sp_spending_insufficient: Liquid funds (要花的钱) -> Cash/Money Market
        - sp_life_insufficient: Insurance (保命的钱) -> Life/Health Insurance
        - sp_growth_insufficient: Growth investments (生钱的钱) -> Stocks/Funds
        - sp_preservation_insufficient: Preservation investments (保本升值的钱) -> Bonds/Fixed Income
        """
        risk_to_category = {
            # Standard & Poor's 4-Quadrant Model risk types (NEW)
            "sp_spending_insufficient": "investment",  # High-liquidity products (money market, cash management)
            "sp_life_insufficient": "insurance",  # Life protection (insurance products)
            "sp_growth_insufficient": "broker",  # Growth investments (stocks, funds, equity)
            "sp_preservation_insufficient": "investment",  # Preservation (bonds, fixed income, stable returns)
            
            # Legacy risk types (backward compatibility)
            "HIGH_RE_CONCENTRATION": "broker",
            "LIQUIDITY_CRISIS": "investment",
            "INSURANCE_GAP": "insurance",
            "DEBT_RISK": "loan",
            "diversification": "broker",
            "liquidity": "investment",
            "insurance": "insurance",
            "保险": "insurance",
            "流动性": "investment",
            "房产": "broker",
        }
        return risk_to_category.get(risk_type)

    def _map_severity_to_priority(self, severity: str) -> str:
        """Map risk severity to action card priority"""
        severity_mapping = {
            "high": "high",
            "medium": "medium",
            "low": "low",
            "critical": "high",
        }
        return severity_mapping.get(severity.lower(), "medium")

    def _create_recommendation_from_product(
        self, product: CommercialProduct, risk_warning: dict[str, Any]
    ) -> dict[str, Any]:
        """Create recommendation object from commercial product and risk warning"""
        return {
            "product_id": product.id,
            "product_name": product.name,
            "provider": product.provider,
            "description": product.description,
            "contact_info": product.contact_info,
            "category": product.category,
            "risk_type": risk_warning.get("type", ""),
            "risk_title": risk_warning.get("title", ""),
            "priority_score": product.priority,
            "recommendation_reason": risk_warning.get("recommendation", ""),
        }

    def _extract_user_tags(self, user_profile: UserProfile) -> list[str]:
        """Extract relevant tags from user profile for product matching"""
        tags = []

        if user_profile.age_range:
            tags.append(f"age_{user_profile.age_range}")

        if user_profile.family_structure:
            tags.append(f"family_{user_profile.family_structure}")

        if user_profile.risk_preference:
            tags.append(f"risk_{user_profile.risk_preference.value}")

        # Add income level tag based on monthly expense
        if user_profile.monthly_expense:
            if user_profile.monthly_expense > 20000:
                tags.append("high_income")
            elif user_profile.monthly_expense > 10000:
                tags.append("medium_income")
            else:
                tags.append("low_income")

        return tags

    def _filter_products_by_user_profile(
        self, products: list[CommercialProduct], user_profile: UserProfile
    ) -> list[CommercialProduct]:
        """Filter products based on user profile matching"""
        user_tags = set(self._extract_user_tags(user_profile))

        # Score products based on tag matching
        scored_products = []
        for product in products:
            product_tags = set(product.target_tags)
            match_score = len(user_tags.intersection(product_tags))
            scored_products.append((product, match_score))

        # Sort by match score (descending) then by priority (descending)
        scored_products.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        return [product for product, _ in scored_products]

    async def track_user_interaction(
        self,
        user_id: int,
        product_id: int,
        interaction_type: str,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ):
        """Track user interaction with recommended products"""
        try:
            from app.core.database import get_db_session
            from app.models.interaction import InteractionType, UserInteraction

            async with get_db_session() as session:
                interaction = UserInteraction(
                    user_id=user_id,
                    product_id=product_id,
                    interaction_type=InteractionType(interaction_type),
                    interaction_metadata=metadata or {},
                    session_id=session_id,
                )

                session.add(interaction)
                await session.commit()

                logger.info(
                    f"Tracked interaction: user={user_id}, product={product_id}, "
                    f"type={interaction_type}, session={session_id}"
                )

        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
            # Don't raise exception - tracking failures shouldn't break the flow


# Global service instance
recommendation_service = RecommendationService()


def get_recommendation_service() -> RecommendationService:
    """Get recommendation service instance"""
    return recommendation_service
