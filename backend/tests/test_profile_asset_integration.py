"""
Tests for user profile and asset integration
Validates requirement 12.3: Associate user profile data with asset data
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AssetType, RiskLevel, User, UserAsset
from app.services.profile_asset_service import ProfileAssetService


class TestProfileAssetIntegration:
    """Test user profile and asset integration"""

    @pytest.mark.asyncio
    async def test_create_profile_with_asset_analysis(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test creating profile with asset analysis"""

        # Create some assets first
        assets = [
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.CASH,
                name="Savings Account",
                value=10000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.INVESTMENT,
                name="Stock Portfolio",
                value=15000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.REAL_ESTATE,
                name="Primary Residence",
                value=300000.0,
                is_confirmed=True,
            ),
        ]

        for asset in assets:
            db_session.add(asset)
        await db_session.commit()

        # Create profile with analysis
        profile_data = {
            "age_range": "26-35",
            "family_structure": "single",
            "risk_preference": RiskLevel.MODERATE,
            "monthly_expense": 3000.0,
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
            user_id_for_audit=test_user.id,
        )

        # Verify profile creation
        assert profile.user_id == test_user.id
        assert profile.age_range == "26-35"
        assert profile.risk_preference == RiskLevel.MODERATE

        # Verify analysis
        assert analysis["total_assets"] == 3
        assert analysis["total_value"] == 325000.0

        # Verify asset breakdown
        breakdown = analysis["asset_breakdown"]
        assert "cash" in breakdown
        assert "investment" in breakdown
        assert "real_estate" in breakdown

        # Check percentages
        assert breakdown["cash"]["percentage"] == pytest.approx(
            3.08, rel=1e-2
        )  # 10k/325k
        assert breakdown["investment"]["percentage"] == pytest.approx(
            4.62, rel=1e-2
        )  # 15k/325k
        assert breakdown["real_estate"]["percentage"] == pytest.approx(
            92.31, rel=1e-2
        )  # 300k/325k

        # Verify recommendations exist
        assert len(analysis["recommendations"]) > 0
        assert isinstance(analysis["risk_analysis"], str)

    @pytest.mark.asyncio
    async def test_analyze_assets_for_conservative_profile(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test asset analysis for conservative risk profile"""

        # Create conservative-friendly assets
        assets = [
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.CASH,
                name="Emergency Fund",
                value=50000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.INSURANCE,
                name="Life Insurance",
                value=20000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.INVESTMENT,
                name="Conservative Bonds",
                value=10000.0,
                is_confirmed=True,
            ),
        ]

        for asset in assets:
            db_session.add(asset)
        await db_session.commit()

        # Create conservative profile
        profile_data = {
            "age_range": "56-65",
            "family_structure": "married_no_children",
            "risk_preference": RiskLevel.CONSERVATIVE,
            "monthly_expense": 4000.0,
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
        )

        # Verify conservative risk analysis
        risk_analysis = analysis["risk_analysis"]
        assert "conservative" in risk_analysis.lower()

        # Verify recommendations include conservative strategies
        recommendations = analysis["recommendations"]
        conservative_keywords = ["capital preservation", "emergency fund", "stability"]
        has_conservative_advice = any(
            any(keyword in rec.lower() for keyword in conservative_keywords)
            for rec in recommendations
        )
        assert has_conservative_advice

    @pytest.mark.asyncio
    async def test_analyze_assets_for_aggressive_profile(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test asset analysis for aggressive risk profile"""

        # Create investment-heavy portfolio
        assets = [
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.INVESTMENT,
                name="Growth Stocks",
                value=80000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.INVESTMENT,
                name="Tech ETF",
                value=40000.0,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=test_user.id,
                asset_type=AssetType.CASH,
                name="Trading Account",
                value=10000.0,
                is_confirmed=True,
            ),
        ]

        for asset in assets:
            db_session.add(asset)
        await db_session.commit()

        # Create aggressive profile
        profile_data = {
            "age_range": "26-35",
            "family_structure": "single",
            "risk_preference": RiskLevel.AGGRESSIVE,
            "monthly_expense": 2500.0,
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
        )

        # Verify aggressive risk analysis
        risk_analysis = analysis["risk_analysis"]
        assert "aggressive" in risk_analysis.lower()

        # Verify high investment percentage
        investment_percentage = analysis["asset_breakdown"]["investment"]["percentage"]
        assert investment_percentage > 80  # Should be over 80% in investments

    @pytest.mark.asyncio
    async def test_update_profile_and_reanalyze(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating profile and getting updated analysis"""

        # Create initial assets
        asset = UserAsset(
            user_id=test_user.id,
            asset_type=AssetType.INVESTMENT,
            name="Stock Portfolio",
            value=50000.0,
            is_confirmed=True,
        )
        db_session.add(asset)
        await db_session.commit()

        # Create initial profile
        initial_profile_data = {
            "age_range": "26-35",
            "family_structure": "single",
            "risk_preference": RiskLevel.AGGRESSIVE,
            "monthly_expense": 2000.0,
        }

        (
            profile,
            initial_analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=initial_profile_data,
        )

        # Update profile to conservative
        updates = {
            "risk_preference": RiskLevel.CONSERVATIVE,
            "age_range": "56-65",
            "monthly_expense": 4000.0,
        }

        (
            updated_profile,
            updated_analysis,
        ) = await ProfileAssetService.update_profile_and_reanalyze(
            db=db_session,
            user=test_user,
            profile_updates=updates,
            user_id_for_audit=test_user.id,
        )

        # Verify profile was updated
        assert updated_profile.risk_preference == RiskLevel.CONSERVATIVE
        assert updated_profile.age_range == "56-65"
        assert updated_profile.monthly_expense == 4000.0

        # Verify analysis changed based on new profile
        assert updated_analysis["risk_analysis"] != initial_analysis["risk_analysis"]
        assert "conservative" in updated_analysis["risk_analysis"].lower()

    @pytest.mark.asyncio
    async def test_emergency_fund_recommendations(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test emergency fund recommendations based on monthly expenses"""

        # Create minimal cash assets
        asset = UserAsset(
            user_id=test_user.id,
            asset_type=AssetType.CASH,
            name="Checking Account",
            value=5000.0,
            is_confirmed=True,
        )
        db_session.add(asset)
        await db_session.commit()

        # Create profile with monthly expenses
        profile_data = {
            "age_range": "26-35",
            "family_structure": "single",
            "risk_preference": RiskLevel.MODERATE,
            "monthly_expense": 3000.0,  # Should recommend 6 months = $18,000
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
        )

        # Verify emergency fund recommendation
        recommendations = analysis["recommendations"]
        emergency_fund_rec = next(
            (rec for rec in recommendations if "emergency fund" in rec.lower()), None
        )

        assert emergency_fund_rec is not None
        assert "18,000" in emergency_fund_rec  # 6 months * $3,000

    @pytest.mark.asyncio
    async def test_family_structure_recommendations(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test recommendations based on family structure"""

        # Create profile with children
        profile_data = {
            "age_range": "36-45",
            "family_structure": "married_with_children",
            "risk_preference": RiskLevel.MODERATE,
            "monthly_expense": 5000.0,
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
        )

        # Verify family-specific recommendations
        recommendations = analysis["recommendations"]
        family_keywords = ["insurance", "children", "education", "family protection"]

        has_family_advice = any(
            any(keyword in rec.lower() for keyword in family_keywords)
            for rec in recommendations
        )
        assert has_family_advice

    @pytest.mark.asyncio
    async def test_no_assets_analysis(self, db_session: AsyncSession, test_user: User):
        """Test analysis when user has no assets"""

        profile_data = {
            "age_range": "18-25",
            "family_structure": "single",
            "risk_preference": RiskLevel.MODERATE,
            "monthly_expense": 2000.0,
        }

        (
            profile,
            analysis,
        ) = await ProfileAssetService.create_profile_with_assets_analysis(
            db=db_session,
            user=test_user,
            profile_data=profile_data,
        )

        # Verify no assets handling
        assert analysis["total_assets"] == 0
        assert analysis["asset_breakdown"] == {}
        assert "No assets to analyze" in analysis["risk_analysis"]

        # Should still provide recommendations
        assert len(analysis["recommendations"]) > 0
        assert any(
            "adding your assets" in rec.lower() for rec in analysis["recommendations"]
        )
