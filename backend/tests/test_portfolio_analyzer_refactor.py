"""
Test the refactored portfolio analyzer logic
"""

import pytest
from app.models.user import AssetType, UserAsset, UserProfile, RiskLevel
from app.services.portfolio_analyzer import (
    portfolio_analyzer,
    SPQuadrant,
    AssetTaxonomy,
    AnalysisStatus,
)


def test_asset_taxonomy_normalization():
    """Test AssetTaxonomy normalization and classification"""
    # Test normalization
    assert AssetTaxonomy.normalize_subtype("  BOND  ") == "bond"
    assert AssetTaxonomy.normalize_subtype("货币基金") == "货币基金"
    assert AssetTaxonomy.normalize_subtype(None) == ""
    assert AssetTaxonomy.normalize_subtype("") == ""

    # Test risk level classification
    assert AssetTaxonomy.get_risk_level_from_subtype("bond") == AssetTaxonomy.RISK_LOW
    assert AssetTaxonomy.get_risk_level_from_subtype("货币基金") == AssetTaxonomy.RISK_LOW
    assert AssetTaxonomy.get_risk_level_from_subtype("stock") == AssetTaxonomy.RISK_HIGH
    assert AssetTaxonomy.get_risk_level_from_subtype("股票") == AssetTaxonomy.RISK_HIGH
    assert (
        AssetTaxonomy.get_risk_level_from_subtype("混合基金")
        == AssetTaxonomy.RISK_MEDIUM
    )
    assert (
        AssetTaxonomy.get_risk_level_from_subtype("unknown")
        == AssetTaxonomy.RISK_MEDIUM
    )  # Default


def test_liquidity_discount_factor_for_real_estate():
    """Test that real estate applies liquidity discount in preservation quadrant"""
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="房产",
            value=1000000,
        ),
    ]

    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=10000,
    )

    # Classify assets
    quadrants = portfolio_analyzer._classify_assets_by_quadrant(assets, user_profile)

    # Real estate should be discounted by liquidity factor (0.8)
    expected_value = 1000000 * AssetTaxonomy.LIQUIDITY_DISCOUNT_REAL_ESTATE
    assert quadrants[SPQuadrant.PRESERVATION_MONEY] == expected_value


def test_data_insufficient_status_no_assets():
    """Test that analysis returns DATA_INSUFFICIENT when no assets provided"""
    assets = []
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=10000,
    )

    analysis = portfolio_analyzer.analyze_portfolio(assets, user_profile)

    assert analysis.status == AnalysisStatus.DATA_INSUFFICIENT
    assert "没有资产数据" in analysis.status_message


def test_zero_monthly_expense_handling():
    """Test that zero or negative monthly expense is handled gracefully"""
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金",
            value=100000,
        ),
    ]

    # Profile with zero monthly expense
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=0,  # Zero expense
    )

    analysis = portfolio_analyzer.analyze_portfolio(assets, user_profile)

    # Should not crash, should use estimation instead
    assert analysis.status == AnalysisStatus.SUCCESS
    assert analysis.liquidity_ratio >= 0  # Should not be infinity


def test_none_monthly_expense_uses_estimation():
    """Test that None monthly expense falls back to estimation"""
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金",
            value=100000,
        ),
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="房产",
            value=5000000,
        ),
    ]

    # Profile with None monthly expense
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=None,
    )

    analysis = portfolio_analyzer.analyze_portfolio(assets, user_profile)

    # Should use estimation
    assert analysis.status == AnalysisStatus.SUCCESS
    assert analysis.liquidity_ratio > 0


def test_safe_metadata_access():
    """Test that asset metadata is accessed safely without crashes"""
    # Asset with no extra_data
    asset1 = UserAsset(
        id=1,
        user_id=1,
        asset_type=AssetType.INVESTMENT,
        name="投资",
        value=100000,
        extra_data=None,
    )

    # Asset with empty extra_data
    asset2 = UserAsset(
        id=2,
        user_id=1,
        asset_type=AssetType.INVESTMENT,
        name="投资2",
        value=100000,
        extra_data={},
    )

    # Asset with malformed subtype
    asset3 = UserAsset(
        id=3,
        user_id=1,
        asset_type=AssetType.INVESTMENT,
        name="投资3",
        value=100000,
        extra_data={"subtype": 123},  # Not a string
    )

    # Should not crash
    subtype1 = portfolio_analyzer._get_asset_subtype(asset1)
    subtype2 = portfolio_analyzer._get_asset_subtype(asset2)
    subtype3 = portfolio_analyzer._get_asset_subtype(asset3)

    assert subtype1 == ""
    assert subtype2 == ""
    assert subtype3 == "123"  # Converted to string and normalized


def test_investment_classification_by_risk_level():
    """Test that investments are classified based on risk level metadata"""

    # Create test assets
    assets = [
        # Low-risk bond investment should go to PRESERVATION
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="国债",
            value=100000,
            extra_data={"risk_level": "low", "subtype": "bond"},
        ),
        # High-risk stock investment should go to GROWTH
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="股票基金",
            value=200000,
            extra_data={"risk_level": "high", "subtype": "stock"},
        ),
        # Money fund should go to PRESERVATION
        UserAsset(
            id=3,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="货币基金",
            value=50000,
            extra_data={"subtype": "money_fund"},
        ),
        # Investment without metadata defaults to GROWTH
        UserAsset(
            id=4,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="未知投资",
            value=150000,
        ),
    ]

    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=10000,
    )

    # Classify assets
    quadrants = portfolio_analyzer._classify_assets_by_quadrant(assets, user_profile)

    # Verify classification
    # Bonds (100k) + Money fund (50k) = 150k in PRESERVATION
    assert quadrants[SPQuadrant.PRESERVATION_MONEY] == 150000

    # Stock fund (200k) + Unknown (150k) = 350k in GROWTH
    assert quadrants[SPQuadrant.GROWTH_MONEY] == 350000


def test_spending_money_includes_debt_servicing():
    """Test that spending money calculation includes debt payments"""
    
    # Create test assets with liability
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金",
            value=200000,
        ),
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=2000000,
            extra_data={"monthly_payment": 10000}  # 10k monthly mortgage
        ),
    ]
    
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=15000  # 15k monthly expense
    )
    
    # Classify assets
    quadrants = portfolio_analyzer._classify_assets_by_quadrant(assets, user_profile)
    
    # Calculate expected spending threshold
    # (15k expense + 10k debt) * 6 months = 150k
    expected_spending = (15000 + 10000) * 6
    
    # Since we have 200k cash, 150k should go to spending, 50k to preservation
    assert quadrants[SPQuadrant.SPENDING_MONEY] == expected_spending
    assert quadrants[SPQuadrant.PRESERVATION_MONEY] == 50000


def test_debt_payment_estimation_without_metadata():
    """Test that debt payment is estimated when metadata is missing"""
    
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=2000000,  # 2M liability
            # No monthly_payment in metadata
        ),
    ]
    
    # Calculate monthly debt payment
    monthly_debt = portfolio_analyzer._calculate_monthly_debt_payment(assets)
    
    # Should estimate as 0.5% of liability value
    expected = 2000000 * 0.005
    assert monthly_debt == expected


def test_spending_money_dynamic_calculation():
    """Test that spending money uses expense-based calculation, not fixed 10%"""
    
    # High net worth scenario
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="房产",
            value=10000000,  # 10M property
        ),
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金",
            value=500000,  # 500k cash
        ),
    ]
    
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="40-50",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.CONSERVATIVE,
        monthly_expense=30000  # Only 30k monthly expense
    )
    
    # Analyze portfolio
    analysis = portfolio_analyzer.analyze_portfolio(assets, user_profile)
    
    # Get spending quadrant analysis
    spending_quadrant = analysis.quadrant_analysis["quadrants"]["spending"]
    
    # Ideal spending should be 6 months of expenses (30k * 6 = 180k)
    # NOT 10% of net worth (which would be ~1M)
    expected_ideal = 30000 * 6
    assert spending_quadrant["ideal_amount"] == expected_ideal
    
    # Verify it's much less than 10% of net worth
    net_worth = analysis.net_worth
    assert spending_quadrant["ideal_amount"] < net_worth * 0.10


def test_full_portfolio_analysis_with_refactored_logic():
    """Integration test for complete portfolio analysis"""
    
    assets = [
        # Cash
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.CASH,
            name="活期存款",
            value=100000,
        ),
        # Real estate
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="自住房",
            value=3000000,
        ),
        # Low-risk investment (should go to preservation)
        UserAsset(
            id=3,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="债券基金",
            value=500000,
            extra_data={"risk_level": "low", "subtype": "bond"}
        ),
        # High-risk investment (should go to growth)
        UserAsset(
            id=4,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="股票",
            value=400000,
            extra_data={"risk_level": "high"}
        ),
        # Insurance
        UserAsset(
            id=5,
            user_id=1,
            asset_type=AssetType.INSURANCE,
            name="重疾险",
            value=50000,
        ),
        # Liability with explicit monthly payment
        UserAsset(
            id=6,
            user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=1500000,
            extra_data={"monthly_payment": 8000}
        ),
    ]
    
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="35-45",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=20000
    )
    
    # Analyze portfolio
    analysis = portfolio_analyzer.analyze_portfolio(assets, user_profile)
    
    # Verify net worth calculation (assets - liabilities)
    expected_net_worth = 100000 + 3000000 + 500000 + 400000 + 50000 - 1500000
    assert analysis.net_worth == expected_net_worth
    
    # Verify quadrant allocations
    quadrants = analysis.quadrant_allocations
    
    # Spending: Should be (20k expense + 8k debt) * 6 = 168k
    # But we only have 100k cash, so spending gets 100k
    assert quadrants[SPQuadrant.SPENDING_MONEY] == 100000
    
    # Life: Insurance = 50k
    assert quadrants[SPQuadrant.LIFE_MONEY] == 50000
    
    # Growth: High-risk stock = 400k
    assert quadrants[SPQuadrant.GROWTH_MONEY] == 400000
    
    # Preservation: Real estate (3M * 0.8 liquidity discount) + Bond (500k) = 2.9M
    expected_preservation = (
        3000000 * AssetTaxonomy.LIQUIDITY_DISCOUNT_REAL_ESTATE + 500000
    )
    assert quadrants[SPQuadrant.PRESERVATION_MONEY] == expected_preservation
    
    # Verify spending money ideal calculation
    spending_analysis = analysis.quadrant_analysis["quadrants"]["spending"]
    expected_ideal_spending = (20000 + 8000) * 6
    assert spending_analysis["ideal_amount"] == expected_ideal_spending
    
    # Verify there's a gap (insufficient spending money)
    assert spending_analysis["gap"] > 0
    assert spending_analysis["status"] == "insufficient"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
