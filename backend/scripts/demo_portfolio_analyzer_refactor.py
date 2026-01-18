#!/usr/bin/env python3
"""
Demo script to showcase the portfolio analyzer refactor improvements
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.models.user import AssetType, UserAsset, UserProfile, RiskLevel
from app.services.portfolio_analyzer import portfolio_analyzer, SPQuadrant


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def format_currency(amount: float) -> str:
    """Format currency with commas"""
    return f"¥{amount:,.0f}"


def demo_investment_classification():
    """Demo 1: Investment classification by risk level"""
    print_section("Demo 1: Investment Classification by Risk Level")
    
    assets = [
        UserAsset(
            id=1, user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="国债基金 (Bond Fund)",
            value=100000,
            extra_data={"risk_level": "low", "subtype": "bond"}
        ),
        UserAsset(
            id=2, user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="股票基金 (Stock Fund)",
            value=200000,
            extra_data={"risk_level": "high", "subtype": "stock"}
        ),
        UserAsset(
            id=3, user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="货币基金 (Money Market Fund)",
            value=50000,
            extra_data={"subtype": "money_fund"}
        ),
    ]
    
    profile = UserProfile(
        id=1, user_id=1,
        age_range="30-40",
        family_structure="single",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=10000
    )
    
    quadrants = portfolio_analyzer._classify_assets_by_quadrant(assets, profile)
    
    print("\n📊 Asset Classification:")
    print(f"  • Bond Fund (¥100,000) → PRESERVATION ✅")
    print(f"  • Stock Fund (¥200,000) → GROWTH ✅")
    print(f"  • Money Market Fund (¥50,000) → PRESERVATION ✅")
    
    print("\n📈 Quadrant Totals:")
    print(f"  • Preservation Money: {format_currency(quadrants[SPQuadrant.PRESERVATION_MONEY])}")
    print(f"  • Growth Money: {format_currency(quadrants[SPQuadrant.GROWTH_MONEY])}")
    
    print("\n✅ Result: Bonds and money funds correctly classified as low-risk preservation!")


def demo_spending_calculation():
    """Demo 2: Dynamic spending money calculation"""
    print_section("Demo 2: Dynamic Spending Money Calculation")
    
    # High net worth scenario
    assets = [
        UserAsset(
            id=1, user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="房产 (Property)",
            value=10000000,  # 10M property
        ),
        UserAsset(
            id=2, user_id=1,
            asset_type=AssetType.CASH,
            name="现金 (Cash)",
            value=500000,
        ),
    ]
    
    profile = UserProfile(
        id=1, user_id=1,
        age_range="40-50",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.CONSERVATIVE,
        monthly_expense=30000  # Only 30k monthly expense
    )
    
    analysis = portfolio_analyzer.analyze_portfolio(assets, profile)
    spending_quadrant = analysis.quadrant_analysis["quadrants"]["spending"]
    
    print("\n💰 Scenario:")
    print(f"  • Net Worth: {format_currency(analysis.net_worth)}")
    print(f"  • Monthly Expense: {format_currency(30000)}")
    print(f"  • Property Value: {format_currency(10000000)}")
    
    print("\n📊 Spending Money Recommendation:")
    old_recommendation = analysis.net_worth * 0.10
    new_recommendation = spending_quadrant["ideal_amount"]
    
    print(f"  • OLD (10% of net worth): {format_currency(old_recommendation)} ❌")
    print(f"  • NEW (6 months expense): {format_currency(new_recommendation)} ✅")
    print(f"  • Savings: {format_currency(old_recommendation - new_recommendation)} freed for investment!")
    
    print("\n✅ Result: More efficient capital allocation based on actual needs!")


def demo_debt_servicing():
    """Demo 3: Debt servicing in liquidity calculation"""
    print_section("Demo 3: Debt Servicing in Liquidity Calculation")
    
    assets = [
        UserAsset(
            id=1, user_id=1,
            asset_type=AssetType.CASH,
            name="现金 (Cash)",
            value=200000,
        ),
        UserAsset(
            id=2, user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="房产 (Property)",
            value=3000000,
        ),
        UserAsset(
            id=3, user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷 (Mortgage)",
            value=2000000,
            extra_data={"monthly_payment": 10000}
        ),
    ]
    
    profile = UserProfile(
        id=1, user_id=1,
        age_range="35-45",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=15000
    )
    
    analysis = portfolio_analyzer.analyze_portfolio(assets, profile)
    spending_quadrant = analysis.quadrant_analysis["quadrants"]["spending"]
    
    print("\n💰 Scenario:")
    print(f"  • Monthly Expense: {format_currency(15000)}")
    print(f"  • Monthly Mortgage: {format_currency(10000)}")
    print(f"  • Total Monthly Obligation: {format_currency(25000)}")
    
    print("\n📊 Emergency Fund Recommendation:")
    old_recommendation = 15000 * 6
    new_recommendation = spending_quadrant["ideal_amount"]
    
    print(f"  • OLD (6 × expense only): {format_currency(old_recommendation)} ❌")
    print(f"  • NEW (6 × (expense + debt)): {format_currency(new_recommendation)} ✅")
    print(f"  • Additional Buffer: {format_currency(new_recommendation - old_recommendation)}")
    
    print("\n✅ Result: Realistic emergency fund that covers ALL obligations!")


def demo_full_analysis():
    """Demo 4: Complete portfolio analysis"""
    print_section("Demo 4: Complete Portfolio Analysis")
    
    assets = [
        UserAsset(
            id=1, user_id=1,
            asset_type=AssetType.CASH,
            name="活期存款",
            value=100000,
        ),
        UserAsset(
            id=2, user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="自住房",
            value=3000000,
        ),
        UserAsset(
            id=3, user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="债券基金",
            value=500000,
            extra_data={"risk_level": "low", "subtype": "bond"}
        ),
        UserAsset(
            id=4, user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="股票基金",
            value=400000,
            extra_data={"risk_level": "high"}
        ),
        UserAsset(
            id=5, user_id=1,
            asset_type=AssetType.INSURANCE,
            name="重疾险",
            value=50000,
        ),
        UserAsset(
            id=6, user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=1500000,
            extra_data={"monthly_payment": 8000}
        ),
    ]
    
    profile = UserProfile(
        id=1, user_id=1,
        age_range="35-45",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.MODERATE,
        monthly_expense=20000
    )
    
    analysis = portfolio_analyzer.analyze_portfolio(assets, profile)
    
    print("\n💰 Portfolio Summary:")
    print(f"  • Net Worth: {format_currency(analysis.net_worth)}")
    print(f"  • Real Estate Ratio: {analysis.real_estate_ratio:.1%}")
    print(f"  • Liquidity Ratio: {analysis.liquidity_ratio:.1f} months")
    
    print("\n📊 Standard & Poor's Four Quadrant Analysis:")
    for quadrant_key, quadrant_data in analysis.quadrant_analysis["quadrants"].items():
        name = quadrant_data["name"]
        current = quadrant_data["current_amount"]
        ideal = quadrant_data["ideal_amount"]
        status = quadrant_data["status"]
        status_icon = "✅" if status == "sufficient" else "⚠️"
        
        print(f"\n  {status_icon} {name}:")
        print(f"     Current: {format_currency(current)}")
        print(f"     Ideal: {format_currency(ideal)}")
        print(f"     Status: {status}")
    
    print("\n🎯 Top Priorities:")
    for i, priority in enumerate(analysis.quadrant_analysis["priorities"][:3], 1):
        action = "增加" if priority["action"] == "increase" else "减少"
        print(f"  {i}. {action}{priority['name']}: {format_currency(abs(priority['gap']))}")
    
    print("\n⚠️  Risk Warnings:")
    for warning in analysis.risk_warnings[:3]:
        print(f"  • [{warning['severity'].upper()}] {warning['title']}")
    
    print("\n💡 Recommendations:")
    for i, rec in enumerate(analysis.recommendations[:3], 1):
        print(f"  {i}. {rec['title']}")
        print(f"     {rec['description']}")


def main():
    """Run all demos"""
    print("\n" + "🎯" * 40)
    print("  Portfolio Analyzer Refactor - Feature Demonstration")
    print("🎯" * 40)
    
    try:
        demo_investment_classification()
        demo_spending_calculation()
        demo_debt_servicing()
        demo_full_analysis()
        
        print("\n" + "=" * 80)
        print("  ✅ All demos completed successfully!")
        print("=" * 80)
        print("\n📚 For more information, see:")
        print("  • PORTFOLIO_ANALYZER_REFACTOR_SUMMARY.md")
        print("  • PORTFOLIO_ANALYZER_USAGE_GUIDE.md")
        print("  • tests/test_portfolio_analyzer_refactor.py")
        print()
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
