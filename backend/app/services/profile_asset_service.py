"""
Service for managing user profile and asset relationships
Implements requirement 12.3: Associate user profile data with asset data
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.audit import AuditAction
from app.models.user import RiskLevel, User, UserAsset, UserProfile
from app.services.audit import AuditService


class ProfileAssetService:
    """Service for managing user profile and asset relationships"""

    @staticmethod
    async def create_profile_with_assets_analysis(
        db: AsyncSession,
        user: User,
        profile_data: dict[str, Any],
        user_id_for_audit: int | None = None,
        **audit_kwargs: Any,
    ) -> tuple[UserProfile, dict[str, Any]]:
        """
        Create user profile and analyze existing assets for recommendations
        Implements requirement 12.3: Associate user profile data with asset data
        """

        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            age_range=profile_data["age_range"],
            family_structure=profile_data["family_structure"],
            risk_preference=profile_data["risk_preference"],
            monthly_expense=profile_data.get("monthly_expense"),
        )

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        # Log profile creation
        await AuditService.log_change(
            db=db,
            table_name="userprofile",
            record_id=profile.id,
            action=AuditAction.CREATE,
            user_id=user_id_for_audit,
            new_values=profile_data,
            **audit_kwargs,
        )

        # Analyze existing assets and provide recommendations
        analysis = await ProfileAssetService.analyze_assets_for_profile(
            db, user, profile
        )

        return profile, analysis

    @staticmethod
    async def analyze_assets_for_profile(
        db: AsyncSession,
        user: User,
        profile: UserProfile,
    ) -> dict[str, Any]:
        """
        Analyze user assets based on their profile and provide insights
        """

        # Get all user assets
        stmt = select(UserAsset).where(UserAsset.user_id == user.id)
        result = await db.execute(stmt)
        assets = result.scalars().all()

        if not assets:
            recommendations = [
                "Start by adding your assets to get personalized recommendations"
            ]

            # Still provide profile-based recommendations even without assets
            if profile.family_structure in ["married_with_children", "single_parent"]:
                recommendations.append(
                    "Ensure adequate insurance coverage for family protection"
                )
                recommendations.append(
                    "Consider education savings for children's future needs"
                )

            if profile.monthly_expense:
                emergency_fund_target = profile.monthly_expense * 6
                recommendations.append(
                    f"Build emergency fund to cover 6 months of expenses (${emergency_fund_target:,.2f})"
                )

            return {
                "total_assets": 0,
                "asset_breakdown": {},
                "risk_analysis": "No assets to analyze",
                "recommendations": recommendations,
            }

        # Calculate asset breakdown
        asset_breakdown = {}
        total_value = 0

        for asset in assets:
            asset_type = asset.asset_type.value  # Keep original enum value (uppercase)
            if asset_type not in asset_breakdown:
                asset_breakdown[asset_type] = {"count": 0, "total_value": 0}

            asset_breakdown[asset_type]["count"] += 1
            asset_breakdown[asset_type]["total_value"] += asset.value
            total_value += asset.value

        # Calculate percentages
        for asset_type in asset_breakdown:
            asset_breakdown[asset_type]["percentage"] = (
                asset_breakdown[asset_type]["total_value"] / total_value * 100
                if total_value > 0
                else 0
            )

        # Risk analysis based on profile
        risk_analysis = ProfileAssetService._analyze_risk_alignment(
            profile.risk_preference, asset_breakdown, total_value
        )

        # Generate recommendations
        recommendations = ProfileAssetService._generate_recommendations(
            profile, asset_breakdown, total_value
        )

        return {
            "total_assets": len(assets),
            "total_value": total_value,
            "asset_breakdown": asset_breakdown,
            "risk_analysis": risk_analysis,
            "recommendations": recommendations,
        }

    @staticmethod
    def _analyze_risk_alignment(
        risk_preference: RiskLevel,
        asset_breakdown: dict[str, Any],
        total_value: float,
    ) -> str:
        """Analyze if asset allocation aligns with risk preference"""

        if total_value == 0:
            return "No assets to analyze"

        # Define risk levels for different asset types
        high_risk_assets = ["investment"]
        medium_risk_assets = ["real_estate"]
        low_risk_assets = ["cash", "insurance"]

        high_risk_percentage = sum(
            asset_breakdown.get(asset_type, {}).get("percentage", 0)
            for asset_type in high_risk_assets
        )

        medium_risk_percentage = sum(
            asset_breakdown.get(asset_type, {}).get("percentage", 0)
            for asset_type in medium_risk_assets
        )

        low_risk_percentage = sum(
            asset_breakdown.get(asset_type, {}).get("percentage", 0)
            for asset_type in low_risk_assets
        )

        if risk_preference == RiskLevel.CONSERVATIVE:
            if low_risk_percentage >= 60:
                return "Your asset allocation aligns well with your conservative risk preference"
            elif high_risk_percentage > 30:
                return (
                    "Your portfolio may be too risky for your conservative preference"
                )
            else:
                return "Consider increasing cash and insurance holdings for better conservative risk alignment"

        elif risk_preference == RiskLevel.MODERATE:
            if 30 <= high_risk_percentage <= 60 and medium_risk_percentage >= 20:
                return (
                    "Your asset allocation is well-balanced for moderate risk tolerance"
                )
            elif high_risk_percentage > 70:
                return (
                    "Your portfolio may be too aggressive for moderate risk preference"
                )
            else:
                return "Consider diversifying with a mix of investments and real estate"

        else:  # AGGRESSIVE
            if high_risk_percentage >= 50:
                return "Your asset allocation matches your aggressive risk preference"
            else:
                return "Consider increasing investment holdings to match your aggressive risk tolerance"

    @staticmethod
    def _generate_recommendations(
        profile: UserProfile,
        asset_breakdown: dict[str, Any],
        total_value: float,
    ) -> list[str]:
        """Generate personalized recommendations based on profile and assets"""

        recommendations = []

        # Age-based recommendations
        if profile.age_range in ["18-25", "26-35"]:
            recommendations.append(
                "Consider increasing investment allocation for long-term growth"
            )
            if asset_breakdown.get("investment", {}).get("percentage", 0) < 40:
                recommendations.append(
                    "Young professionals typically benefit from 40-60% investment allocation"
                )

        elif profile.age_range in ["36-45", "46-55"]:
            recommendations.append(
                "Balance growth investments with stability as you approach peak earning years"
            )
            if asset_breakdown.get("real_estate", {}).get("percentage", 0) < 20:
                recommendations.append(
                    "Consider real estate investment for portfolio diversification"
                )

        else:  # 56+ or retirement age
            recommendations.append(
                "Focus on capital preservation and income generation"
            )
            if asset_breakdown.get("cash", {}).get("percentage", 0) < 20:
                recommendations.append("Maintain adequate cash reserves for stability")

        # Family structure recommendations
        if profile.family_structure in ["married_with_children", "single_parent"]:
            if asset_breakdown.get("insurance", {}).get("percentage", 0) < 10:
                recommendations.append(
                    "Ensure adequate insurance coverage for family protection"
                )
            recommendations.append(
                "Consider education savings for children's future needs"
            )

        # Monthly expense recommendations
        if profile.monthly_expense:
            emergency_fund_target = profile.monthly_expense * 6
            cash_amount = asset_breakdown.get("cash", {}).get("total_value", 0)

            if cash_amount < emergency_fund_target:
                recommendations.append(
                    f"Build emergency fund to cover 6 months of expenses (${emergency_fund_target:,.2f})"
                )

        # Risk-specific recommendations
        if profile.risk_preference == RiskLevel.CONSERVATIVE:
            recommendations.append(
                "Focus on capital preservation with bonds and high-yield savings"
            )
        elif profile.risk_preference == RiskLevel.MODERATE:
            recommendations.append(
                "Maintain balanced portfolio with mix of stocks, bonds, and real estate"
            )
        else:  # AGGRESSIVE
            recommendations.append(
                "Consider growth stocks and alternative investments for higher returns"
            )

        # Asset diversification recommendations
        if len(asset_breakdown) < 3:
            recommendations.append(
                "Diversify across different asset types to reduce risk"
            )

        # Liability management
        if "liability" in asset_breakdown:
            liability_percentage = asset_breakdown["liability"]["percentage"]
            if liability_percentage > 30:
                recommendations.append("Consider strategies to reduce high debt burden")

        return recommendations[:5]  # Limit to top 5 recommendations

    @staticmethod
    async def update_profile_and_reanalyze(
        db: AsyncSession,
        user: User,
        profile_updates: dict[str, Any],
        user_id_for_audit: int | None = None,
        **audit_kwargs: Any,
    ) -> tuple[UserProfile, dict[str, Any]]:
        """Update user profile and re-analyze asset recommendations"""

        # Get existing profile
        stmt = select(UserProfile).where(UserProfile.user_id == user.id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise ValueError("User profile not found")

        # Store old values for audit
        old_values = {
            "age_range": profile.age_range,
            "family_structure": profile.family_structure,
            "risk_preference": profile.risk_preference.value,
            "monthly_expense": profile.monthly_expense,
        }

        # Update profile
        for field, value in profile_updates.items():
            if hasattr(profile, field):
                setattr(profile, field, value)

        await db.commit()
        await db.refresh(profile)

        # Store new values for audit
        new_values = {
            "age_range": profile.age_range,
            "family_structure": profile.family_structure,
            "risk_preference": profile.risk_preference.value,
            "monthly_expense": profile.monthly_expense,
        }

        # Log profile update
        await AuditService.log_change(
            db=db,
            table_name="userprofile",
            record_id=profile.id,
            action=AuditAction.UPDATE,
            user_id=user_id_for_audit,
            old_values=old_values,
            new_values=new_values,
            **audit_kwargs,
        )

        # Re-analyze assets with updated profile
        analysis = await ProfileAssetService.analyze_assets_for_profile(
            db, user, profile
        )

        return profile, analysis
