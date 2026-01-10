"""
Tests for portfolio analyzer functionality
"""

import pytest

from app.models.user import AssetType, UserAsset, UserProfile
from app.services.portfolio_analyzer import PortfolioAnalyzer, RiskLevel


class TestPortfolioAnalyzer:
    """Test portfolio analysis functionality"""

    def test_basic_portfolio_analysis(self):
        """Test basic portfolio analysis with sample assets"""
        analyzer = PortfolioAnalyzer()

        # Create sample assets
        assets = [
            UserAsset(
                user_id=1,
                asset_type=AssetType.REAL_ESTATE,
                name="北京房产",
                value=5000000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.CASH,
                name="现金储蓄",
                value=200000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.LIABILITY,
                name="房贷",
                value=2000000,
                is_confirmed=True,
            ),
        ]

        # Create sample profile
        profile = UserProfile(
            user_id=1,
            age_range="30-40",
            family_structure="married_with_kids",
            monthly_expense=15000,
            risk_preference="moderate",
        )

        # Perform analysis
        analysis = analyzer.analyze_portfolio(assets, profile)

        # Verify basic calculations
        assert analysis.net_worth == 3200000  # 5M + 200K - 2M
        assert analysis.real_estate_ratio == pytest.approx(5000000 / 3200000, rel=1e-3)
        assert analysis.liquidity_ratio == pytest.approx(200000 / 15000, rel=1e-3)

        # Should have risk warnings due to high real estate ratio and low liquidity
        assert len(analysis.risk_warnings) > 0
        assert any(
            w["type"] == "real_estate_concentration" for w in analysis.risk_warnings
        )
        assert any(w["type"] == "liquidity_risk" for w in analysis.risk_warnings)

        # Should have recommendations
        assert len(analysis.recommendations) > 0

        # Overall risk should be medium or high
        assert analysis.overall_risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]

    def test_balanced_portfolio_analysis(self):
        """Test analysis of a well-balanced portfolio"""
        analyzer = PortfolioAnalyzer()

        # Create balanced assets
        assets = [
            UserAsset(
                user_id=1,
                asset_type=AssetType.REAL_ESTATE,
                name="房产",
                value=2000000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.CASH,
                name="现金",
                value=300000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.INVESTMENT,
                name="股票基金",
                value=700000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.INSURANCE,
                name="重疾险",
                value=50000,
                is_confirmed=True,
            ),
        ]

        profile = UserProfile(
            user_id=1,
            age_range="35-45",
            family_structure="married",
            monthly_expense=10000,
            risk_preference="moderate",
        )

        analysis = analyzer.analyze_portfolio(assets, profile)

        # Net worth should be sum of all assets
        assert analysis.net_worth == 3050000

        # Real estate ratio should be reasonable
        assert analysis.real_estate_ratio == pytest.approx(2000000 / 3050000, rel=1e-3)
        assert analysis.real_estate_ratio < 0.75  # Should be under threshold

        # Liquidity should be good
        assert analysis.liquidity_ratio == pytest.approx(300000 / 10000, rel=1e-3)
        assert analysis.liquidity_ratio > 3.0  # Should be above threshold

        # Should have fewer warnings
        assert len(analysis.risk_warnings) <= 1

        # Overall risk should be low or medium
        assert analysis.overall_risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_threshold_adjustment_by_age(self):
        """Test that thresholds are adjusted based on user age"""
        analyzer = PortfolioAnalyzer()

        # Young user profile
        young_profile = UserProfile(
            user_id=1,
            age_range="25-35",
            family_structure="single",
            risk_preference="moderate",
        )

        # Older user profile
        older_profile = UserProfile(
            user_id=2,
            age_range="55-65",
            family_structure="married",
            risk_preference="moderate",
        )

        young_thresholds = analyzer._adjust_thresholds_for_user(young_profile)
        older_thresholds = analyzer._adjust_thresholds_for_user(older_profile)

        # Young users should have higher real estate tolerance
        assert young_thresholds["real_estate_max"] > older_thresholds["real_estate_max"]

        # Older users should need more liquidity
        assert older_thresholds["liquidity_min"] > young_thresholds["liquidity_min"]

    def test_analysis_summary_generation(self):
        """Test generation of human-readable analysis summary"""
        analyzer = PortfolioAnalyzer()

        assets = [
            UserAsset(
                user_id=1,
                asset_type=AssetType.REAL_ESTATE,
                name="房产",
                value=3000000,
                is_confirmed=True,
            ),
            UserAsset(
                user_id=1,
                asset_type=AssetType.CASH,
                name="现金",
                value=500000,
                is_confirmed=True,
            ),
        ]

        analysis = analyzer.analyze_portfolio(assets)
        summary = analyzer.generate_analysis_summary(analysis)

        # Summary should contain key information
        assert "净资产" in summary
        assert "房产占比" in summary
        assert "流动性储备" in summary
        assert "风险水平" in summary

        # Should be properly formatted Chinese text
        assert summary.endswith("。")
        assert len(summary) > 50  # Should be reasonably detailed
