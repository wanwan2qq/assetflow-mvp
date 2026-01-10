"""
Property-based tests for portfolio analyzer functionality

Tests Property 2: 财务指标计算正确性
Tests Property 3: 风险阈值触发正确性
Tests Property 10: 个性化阈值调整正确性
Tests Property 13: 标准普尔四象限分类正确性 (NEW)
Tests Property 14: 四象限配置比例计算正确性 (NEW)
"""

from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.models.user import AssetType, RiskLevel, UserAsset, UserProfile
from app.services.portfolio_analyzer import PortfolioAnalyzer, SPQuadrant


# Hypothesis strategies for generating test data
@composite
def valid_asset_values(draw):
    """Generate valid asset values"""
    return draw(st.floats(min_value=1000.0, max_value=100000000.0))


@composite
def valid_monthly_expenses(draw):
    """Generate valid monthly expense values"""
    return draw(st.floats(min_value=1000.0, max_value=500000.0))


@composite
def user_asset_data(draw):
    """Generate user asset data for testing"""
    asset_type = draw(st.sampled_from(list(AssetType)))
    name = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Po", "Zs")),
        )
    )
    value = draw(valid_asset_values())

    return {
        "asset_type": asset_type,
        "name": name.strip() or "Test Asset",
        "value": value,
        "is_confirmed": draw(st.booleans()),
        "user_id": 1,
    }


@composite
def user_profile_data(draw):
    """Generate user profile data for testing"""
    age_ranges = ["20-30", "30-40", "40-50", "50-60", "60+"]
    family_structures = [
        "single",
        "married",
        "married_with_kids",
        "divorced",
        "widowed",
    ]

    return {
        "user_id": 1,
        "age_range": draw(st.sampled_from(age_ranges)),
        "family_structure": draw(st.sampled_from(family_structures)),
        "risk_preference": draw(st.sampled_from(list(RiskLevel))),
        "monthly_expense": draw(st.one_of(st.none(), valid_monthly_expenses())),
    }


@composite
def portfolio_test_data(draw):
    """Generate complete portfolio test data"""
    # Generate 1-10 assets
    num_assets = draw(st.integers(min_value=1, max_value=10))
    assets_data = draw(
        st.lists(user_asset_data(), min_size=num_assets, max_size=num_assets)
    )

    # Ensure we have at least one non-liability asset for meaningful calculations
    has_positive_asset = any(
        asset["asset_type"] != AssetType.LIABILITY for asset in assets_data
    )
    assume(has_positive_asset)

    # Generate user profile (optional)
    profile_data = draw(st.one_of(st.none(), user_profile_data()))

    return assets_data, profile_data


class TestPortfolioProperties:
    """
    Property-based tests for portfolio analyzer correctness
    """

    # **Feature: asset-flow-mvp, Property 2: 财务指标计算正确性**
    @given(portfolio_data=portfolio_test_data())
    @settings(max_examples=100)
    def test_financial_metrics_calculation_correctness(self, portfolio_data):
        """
        For any user asset portfolio, the configuration engine should calculate
        net worth, real estate ratio, and liquidity ratio according to strict
        mathematical formulas: net worth = real estate + cash + investment - liabilities,
        real estate ratio = real estate value / net worth,
        liquidity ratio = cash / (6 × monthly expenses)

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        assets_data, profile_data = portfolio_data

        # Create UserAsset objects
        assets = [UserAsset(**asset_data) for asset_data in assets_data]

        # Create UserProfile if provided
        profile = UserProfile(**profile_data) if profile_data else None

        # Perform analysis
        analyzer = PortfolioAnalyzer()
        analysis = analyzer.analyze_portfolio(assets, profile)

        # Calculate expected values manually
        total_assets = 0.0
        total_liabilities = 0.0
        real_estate_value = 0.0
        cash_value = 0.0

        for asset in assets:
            if asset.asset_type == AssetType.LIABILITY:
                total_liabilities += asset.value
            else:
                total_assets += asset.value
                if asset.asset_type == AssetType.REAL_ESTATE:
                    real_estate_value += asset.value
                elif asset.asset_type == AssetType.CASH:
                    cash_value += asset.value

        expected_net_worth = total_assets - total_liabilities

        # Verify net worth calculation
        assert abs(analysis.net_worth - expected_net_worth) < 0.01, (
            f"Net worth mismatch: expected {expected_net_worth}, got {analysis.net_worth}"
        )

        # Verify real estate ratio calculation
        if expected_net_worth > 0:
            expected_re_ratio = real_estate_value / expected_net_worth
            assert abs(analysis.real_estate_ratio - expected_re_ratio) < 0.001, (
                f"Real estate ratio mismatch: expected {expected_re_ratio}, got {analysis.real_estate_ratio}"
            )
        else:
            assert analysis.real_estate_ratio == 0.0

        # Verify liquidity ratio calculation
        if profile and profile.monthly_expense and profile.monthly_expense > 0:
            expected_liquidity_ratio = cash_value / profile.monthly_expense
            assert abs(analysis.liquidity_ratio - expected_liquidity_ratio) < 0.001, (
                f"Liquidity ratio mismatch: expected {expected_liquidity_ratio}, got {analysis.liquidity_ratio}"
            )

    # **Feature: asset-flow-mvp, Property 3: 风险阈值触发正确性**
    @given(
        real_estate_ratio=st.floats(min_value=0.0, max_value=0.95),
        liquidity_ratio=st.floats(min_value=0.0, max_value=50.0),
        has_liabilities=st.booleans(),
        has_insurance=st.booleans(),
    )
    @settings(max_examples=100)
    def test_risk_threshold_trigger_correctness(
        self, real_estate_ratio, liquidity_ratio, has_liabilities, has_insurance
    ):
        """
        For any portfolio health data, when real estate ratio exceeds 75%,
        liquidity ratio is below 3, or liabilities exist without insurance,
        the system should generate corresponding risk warnings with warning
        types that precisely match the triggering conditions

        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        analyzer = PortfolioAnalyzer()

        # Create assets to achieve the desired ratios more precisely
        monthly_expense = 10000.0
        cash_value = liquidity_ratio * monthly_expense

        # Calculate total asset value (before liabilities)
        total_asset_value = 1000000.0
        real_estate_value = real_estate_ratio * total_asset_value

        # Calculate remaining value for other assets
        remaining_value = total_asset_value - real_estate_value - cash_value

        # Account for insurance in the remaining value
        insurance_value = 50000.0 if has_insurance else 0.0
        remaining_value -= insurance_value

        # Skip cases where remaining value would be negative
        assume(remaining_value >= 0)

        assets = []

        # Add real estate if needed
        if real_estate_value > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.REAL_ESTATE,
                    name="Test Property",
                    value=real_estate_value,
                    is_confirmed=True,
                )
            )

        # Add cash if needed
        if cash_value > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.CASH,
                    name="Test Cash",
                    value=cash_value,
                    is_confirmed=True,
                )
            )

        # Add other assets to reach target total
        if remaining_value > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.INVESTMENT,
                    name="Test Investment",
                    value=remaining_value,
                    is_confirmed=True,
                )
            )

        # Add insurance if specified
        if has_insurance:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.INSURANCE,
                    name="Test Insurance",
                    value=insurance_value,
                    is_confirmed=True,
                )
            )

        # Add liabilities if specified (this will change net worth)
        liability_value = 100000.0 if has_liabilities else 0.0
        if has_liabilities:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.LIABILITY,
                    name="Test Liability",
                    value=liability_value,
                    is_confirmed=True,
                )
            )

        # Create profile with known monthly expense
        profile = UserProfile(
            user_id=1,
            age_range="30-40",
            family_structure="single",
            risk_preference=RiskLevel.MODERATE,
            monthly_expense=monthly_expense,
        )

        # Perform analysis
        analysis = analyzer.analyze_portfolio(assets, profile)
        thresholds = analyzer._adjust_thresholds_for_user(profile)

        # Check risk warnings based on actual calculated ratios and thresholds
        warning_types = [w["type"] for w in analysis.risk_warnings]

        # Real estate concentration warning
        if analysis.real_estate_ratio > thresholds["real_estate_max"]:
            assert "real_estate_concentration" in warning_types, (
                f"Expected real estate concentration warning for ratio {analysis.real_estate_ratio:.3f} > {thresholds['real_estate_max']}"
            )

        # Liquidity risk warning
        if analysis.liquidity_ratio < thresholds["liquidity_min"]:
            assert "liquidity_risk" in warning_types, (
                f"Expected liquidity risk warning for ratio {analysis.liquidity_ratio:.3f} < {thresholds['liquidity_min']}"
            )

        # Insurance gap warning
        if has_liabilities and not has_insurance:
            assert "insurance_gap" in warning_types, (
                "Expected insurance gap warning when liabilities exist without insurance"
            )

    # **Feature: asset-flow-mvp, Property 10: 个性化阈值调整正确性**
    @given(profile_data=user_profile_data())
    @settings(max_examples=100)
    def test_personalized_threshold_adjustment_correctness(self, profile_data):
        """
        For any user profile data (age range, family structure, risk preference),
        the configuration engine should dynamically adjust risk thresholds according
        to predefined rules: younger users allow higher risk asset ratios,
        conservative users have lower risk tolerance

        **Validates: Requirements 12.2, 12.4**
        """
        analyzer = PortfolioAnalyzer()
        profile = UserProfile(**profile_data)

        # Get adjusted thresholds
        thresholds = analyzer._adjust_thresholds_for_user(profile)

        # Verify threshold adjustments based on age (when not overridden by risk preference)
        if profile.age_range in ["20-30", "25-35", "30-40"]:
            # Young users should generally have higher real estate tolerance
            # unless they are conservative
            if profile.risk_preference != RiskLevel.CONSERVATIVE:
                assert thresholds["real_estate_max"] >= 0.75, (
                    f"Young non-conservative users should have at least 75% real estate threshold, got {thresholds['real_estate_max']}"
                )
        elif profile.age_range in ["50-60", "55-65", "60+"]:
            # Older users should be more conservative unless they are aggressive
            if profile.risk_preference != RiskLevel.AGGRESSIVE:
                assert thresholds["real_estate_max"] <= 0.75, (
                    f"Older non-aggressive users should have at most 75% real estate threshold, got {thresholds['real_estate_max']}"
                )

        # Verify threshold adjustments based on family structure
        if profile.family_structure == "married_with_kids":
            # Families need more liquidity regardless of other factors
            assert thresholds["liquidity_min"] >= 15.0, (
                f"Families with kids should need at least 15 months liquidity, got {thresholds['liquidity_min']}"
            )

        # Verify threshold adjustments based on risk preference
        if profile.risk_preference == RiskLevel.CONSERVATIVE:
            # Conservative users should have stricter thresholds
            assert thresholds["real_estate_max"] <= 0.60, (
                f"Conservative users should have max 60% real estate, got {thresholds['real_estate_max']}"
            )
            assert thresholds["liquidity_min"] >= 5.0, (
                f"Conservative users should need at least 5 months liquidity, got {thresholds['liquidity_min']}"
            )
        elif profile.risk_preference == RiskLevel.AGGRESSIVE:
            # Aggressive users can take more risk with real estate
            assert thresholds["real_estate_max"] >= 0.80, (
                f"Aggressive users should allow at least 80% real estate, got {thresholds['real_estate_max']}"
            )
            # But families with kids still need high liquidity even if aggressive
            if profile.family_structure != "married_with_kids":
                assert thresholds["liquidity_min"] <= 4.0, (
                    f"Aggressive non-family users should allow lower liquidity, got {thresholds['liquidity_min']}"
                )

        # All thresholds should be reasonable
        assert 0.0 < thresholds["real_estate_max"] <= 1.0, (
            f"Real estate max threshold should be between 0 and 1, got {thresholds['real_estate_max']}"
        )
        assert thresholds["liquidity_min"] > 0.0, (
            f"Liquidity min threshold should be positive, got {thresholds['liquidity_min']}"
        )
        assert 0.0 < thresholds["debt_to_asset_max"] <= 1.0, (
            f"Debt to asset max threshold should be between 0 and 1, got {thresholds['debt_to_asset_max']}"
        )

    # Additional property test for calculation consistency
    @given(
        assets_data=st.lists(user_asset_data(), min_size=1, max_size=5),
        profile_data=st.one_of(st.none(), user_profile_data()),
    )
    @settings(max_examples=50)
    def test_analysis_consistency_across_calls(self, assets_data, profile_data):
        """
        For any portfolio, multiple analysis calls with the same data
        should produce identical results (deterministic behavior)
        """
        # Ensure we have at least one non-liability asset
        has_positive_asset = any(
            asset["asset_type"] != AssetType.LIABILITY for asset in assets_data
        )
        assume(has_positive_asset)

        assets = [UserAsset(**asset_data) for asset_data in assets_data]
        profile = UserProfile(**profile_data) if profile_data else None

        analyzer = PortfolioAnalyzer()

        # Perform analysis twice
        analysis1 = analyzer.analyze_portfolio(assets, profile)
        analysis2 = analyzer.analyze_portfolio(assets, profile)

        # Results should be identical
        assert analysis1.net_worth == analysis2.net_worth
        assert analysis1.real_estate_ratio == analysis2.real_estate_ratio
        assert analysis1.liquidity_ratio == analysis2.liquidity_ratio
        assert len(analysis1.risk_warnings) == len(analysis2.risk_warnings)
        assert len(analysis1.recommendations) == len(analysis2.recommendations)
        assert analysis1.overall_risk_level == analysis2.overall_risk_level

    # **Feature: asset-flow-mvp, Property 13: 标准普尔四象限分类正确性**
    @given(
        cash_amount=st.floats(min_value=10000.0, max_value=1000000.0),
        monthly_expense=st.floats(min_value=5000.0, max_value=50000.0),
        insurance_amount=st.floats(min_value=0.0, max_value=500000.0),
        investment_amount=st.floats(min_value=0.0, max_value=2000000.0),
        real_estate_amount=st.floats(min_value=0.0, max_value=10000000.0),
    )
    @settings(max_examples=50)
    def test_sp_quadrant_classification_correctness(
        self,
        cash_amount,
        monthly_expense,
        insurance_amount,
        investment_amount,
        real_estate_amount,
    ):
        """
        For any asset portfolio, the Standard & Poor's four quadrant classification
        should correctly categorize assets: cash up to 6 months expenses goes to spending money,
        excess cash and real estate go to preservation money, insurance goes to life money,
        investments go to growth money

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        analyzer = PortfolioAnalyzer()

        # Create assets
        assets = []
        if cash_amount > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.CASH,
                    name="Test Cash",
                    value=cash_amount,
                    is_confirmed=True,
                )
            )

        if insurance_amount > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.INSURANCE,
                    name="Test Insurance",
                    value=insurance_amount,
                    is_confirmed=True,
                )
            )

        if investment_amount > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.INVESTMENT,
                    name="Test Investment",
                    value=investment_amount,
                    is_confirmed=True,
                )
            )

        if real_estate_amount > 0:
            assets.append(
                UserAsset(
                    user_id=1,
                    asset_type=AssetType.REAL_ESTATE,
                    name="Test Real Estate",
                    value=real_estate_amount,
                    is_confirmed=True,
                )
            )

        # Create profile with known monthly expense
        profile = UserProfile(
            user_id=1,
            age_range="30-40",
            family_structure="single",
            risk_preference=RiskLevel.MODERATE,
            monthly_expense=monthly_expense,
        )

        # Perform classification
        quadrant_allocations = analyzer._classify_assets_by_quadrant(assets, profile)

        # Verify spending money classification
        spending_threshold = monthly_expense * 6
        expected_spending = min(cash_amount, spending_threshold)
        assert (
            abs(quadrant_allocations[SPQuadrant.SPENDING_MONEY] - expected_spending)
            < 0.01
        ), (
            f"Spending money mismatch: expected {expected_spending}, got {quadrant_allocations[SPQuadrant.SPENDING_MONEY]}"
        )

        # Verify life money classification
        assert (
            abs(quadrant_allocations[SPQuadrant.LIFE_MONEY] - insurance_amount) < 0.01
        ), (
            f"Life money mismatch: expected {insurance_amount}, got {quadrant_allocations[SPQuadrant.LIFE_MONEY]}"
        )

        # Verify growth money classification
        assert (
            abs(quadrant_allocations[SPQuadrant.GROWTH_MONEY] - investment_amount)
            < 0.01
        ), (
            f"Growth money mismatch: expected {investment_amount}, got {quadrant_allocations[SPQuadrant.GROWTH_MONEY]}"
        )

        # Verify preservation money classification
        excess_cash = max(0, cash_amount - spending_threshold)
        expected_preservation = excess_cash + real_estate_amount
        assert (
            abs(
                quadrant_allocations[SPQuadrant.PRESERVATION_MONEY]
                - expected_preservation
            )
            < 0.01
        ), (
            f"Preservation money mismatch: expected {expected_preservation}, got {quadrant_allocations[SPQuadrant.PRESERVATION_MONEY]}"
        )

    # **Feature: asset-flow-mvp, Property 14: 四象限配置比例计算正确性**
    @given(profile_data=user_profile_data())
    @settings(max_examples=50)
    def test_sp_allocation_ratio_calculation_correctness(self, profile_data):
        """
        For any user profile, the ideal Standard & Poor's allocation ratios should
        sum to 1.0 and be adjusted correctly based on user characteristics:
        young users have higher growth allocation, families have higher spending/life allocation,
        conservative users have higher preservation allocation

        **Validates: Requirements 12.2, 12.4**
        """
        analyzer = PortfolioAnalyzer()
        profile = UserProfile(**profile_data)

        # Get ideal allocations
        ideal_allocations = analyzer._calculate_ideal_sp_allocations(profile)

        # Verify allocations sum to 1.0
        total_allocation = sum(ideal_allocations.values())
        assert abs(total_allocation - 1.0) < 0.001, (
            f"Allocations should sum to 1.0, got {total_allocation}"
        )

        # Verify all allocations are positive
        for quadrant, allocation in ideal_allocations.items():
            assert allocation > 0, (
                f"{quadrant} allocation should be positive, got {allocation}"
            )
            assert allocation < 1.0, (
                f"{quadrant} allocation should be less than 1.0, got {allocation}"
            )

        # Verify age-based adjustments (only if not overridden by family structure or risk preference)
        if (
            profile.age_range in ["20-30", "25-35"]
            and profile.risk_preference != RiskLevel.CONSERVATIVE
            and profile.family_structure != "married_with_kids"
        ):
            # Young non-conservative non-family users should have higher growth allocation
            assert ideal_allocations[SPQuadrant.GROWTH_MONEY] >= 0.35, (
                f"Young non-conservative non-family users should have at least 35% growth allocation, got {ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}"
            )
        elif (
            profile.age_range in ["50-60", "55-65", "60+"]
            and profile.risk_preference != RiskLevel.AGGRESSIVE
            and profile.family_structure != "married_with_kids"
        ):
            # Older non-aggressive non-family users should have higher preservation allocation
            assert ideal_allocations[SPQuadrant.PRESERVATION_MONEY] >= 0.44, (
                f"Older non-aggressive non-family users should have at least 44% preservation allocation, got {ideal_allocations[SPQuadrant.PRESERVATION_MONEY]:.1%}"
            )

        # Verify family structure adjustments (has priority over age and some risk preferences)
        if profile.family_structure == "married_with_kids":
            # Families should have higher spending and life allocations
            assert ideal_allocations[SPQuadrant.SPENDING_MONEY] >= 0.10, (
                f"Families should have at least 10% spending allocation, got {ideal_allocations[SPQuadrant.SPENDING_MONEY]:.1%}"
            )
            assert ideal_allocations[SPQuadrant.LIFE_MONEY] >= 0.20, (
                f"Families should have at least 20% life allocation, got {ideal_allocations[SPQuadrant.LIFE_MONEY]:.1%}"
            )

        # Verify risk preference adjustments
        if profile.risk_preference == RiskLevel.CONSERVATIVE:
            # Conservative users should have lower growth, higher preservation
            assert ideal_allocations[SPQuadrant.GROWTH_MONEY] <= 0.20, (
                f"Conservative users should have at most 20% growth allocation, got {ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}"
            )
            assert ideal_allocations[SPQuadrant.PRESERVATION_MONEY] >= 0.40, (
                f"Conservative users should have at least 40% preservation allocation, got {ideal_allocations[SPQuadrant.PRESERVATION_MONEY]:.1%}"
            )
        elif profile.risk_preference == RiskLevel.AGGRESSIVE:
            # Aggressive users should have higher growth allocation, but families have constraints
            if profile.family_structure == "married_with_kids":
                # Aggressive families still need safety, so growth is reduced
                assert ideal_allocations[SPQuadrant.GROWTH_MONEY] >= 0.30, (
                    f"Aggressive families should have at least 30% growth allocation, got {ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}"
                )
            else:
                # Aggressive non-families can be more aggressive
                assert ideal_allocations[SPQuadrant.GROWTH_MONEY] >= 0.40, (
                    f"Aggressive non-family users should have at least 40% growth allocation, got {ideal_allocations[SPQuadrant.GROWTH_MONEY]:.1%}"
                )

    # **Feature: asset-flow-mvp, Property 15: 四象限分析完整性**
    @given(portfolio_data=portfolio_test_data())
    @settings(max_examples=30)
    def test_sp_quadrant_analysis_completeness(self, portfolio_data):
        """
        For any portfolio analysis, the Standard & Poor's quadrant analysis should
        be complete with all required fields: quadrants, summary, priorities,
        and allocation gaps should be calculated correctly

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        assets_data, profile_data = portfolio_data

        # Ensure we have at least one non-liability asset
        has_positive_asset = any(
            asset["asset_type"] != AssetType.LIABILITY for asset in assets_data
        )
        assume(has_positive_asset)

        assets = [UserAsset(**asset_data) for asset_data in assets_data]
        profile = UserProfile(**profile_data) if profile_data else None

        analyzer = PortfolioAnalyzer()
        analysis = analyzer.analyze_portfolio(assets, profile)

        # Verify quadrant analysis structure
        assert analysis.quadrant_analysis is not None, (
            "Quadrant analysis should not be None"
        )
        assert "quadrants" in analysis.quadrant_analysis, (
            "Should have quadrants section"
        )
        assert "summary" in analysis.quadrant_analysis, "Should have summary section"
        assert "priorities" in analysis.quadrant_analysis, (
            "Should have priorities section"
        )

        # Verify all four quadrants are present
        quadrants = analysis.quadrant_analysis["quadrants"]
        expected_quadrants = {q.value for q in SPQuadrant}
        actual_quadrants = set(quadrants.keys())
        assert actual_quadrants == expected_quadrants, (
            f"Should have all four quadrants, missing: {expected_quadrants - actual_quadrants}"
        )

        # Verify quadrant data structure
        for quadrant_key, quadrant_data in quadrants.items():
            required_fields = [
                "name",
                "current_amount",
                "ideal_amount",
                "current_ratio",
                "ideal_ratio",
                "gap",
                "status",
            ]
            for field in required_fields:
                assert field in quadrant_data, (
                    f"Quadrant {quadrant_key} should have {field} field"
                )

            # Verify data types and ranges
            assert isinstance(quadrant_data["current_amount"], (int, float)), (
                "current_amount should be numeric"
            )
            assert isinstance(quadrant_data["ideal_amount"], (int, float)), (
                "ideal_amount should be numeric"
            )
            assert 0 <= quadrant_data["current_ratio"] <= 1, (
                "current_ratio should be between 0 and 1"
            )
            assert 0 <= quadrant_data["ideal_ratio"] <= 1, (
                "ideal_ratio should be between 0 and 1"
            )
            assert quadrant_data["status"] in ["sufficient", "insufficient"], (
                "status should be valid"
            )

        # Verify allocation consistency
        total_ideal = sum(analysis.ideal_allocations.values())

        assert abs(total_ideal - 1.0) < 0.001, (
            f"Ideal allocations should sum to 1.0, got {total_ideal}"
        )

        # Verify gaps calculation
        for quadrant in SPQuadrant:
            expected_gap = (
                analysis.ideal_allocations[quadrant] * analysis.net_worth
                - analysis.quadrant_allocations[quadrant]
            )
            actual_gap = analysis.allocation_gaps[quadrant]
            assert abs(actual_gap - expected_gap) < 0.01, (
                f"Gap calculation error for {quadrant}: expected {expected_gap}, got {actual_gap}"
            )
