"""
ActionReasoner Test Script

Tests the action plan generation functionality.

Usage:
    python -m scripts.test_action_reasoner
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_action_reasoner():
    """Test ActionReasoner plan generation"""
    from app.services.action_reasoner import get_action_reasoner
    from app.core.config import get_settings
    
    settings = get_settings()
    print(f"\n🔧 Configuration:")
    print(f"   ENABLE_ACTION_REASONER = {settings.ENABLE_ACTION_REASONER}")
    print(f"   ACTION_PLAN_AUTO_GENERATE = {settings.ACTION_PLAN_AUTO_GENERATE}")
    
    if not settings.ENABLE_ACTION_REASONER:
        print("❌ ActionReasoner is disabled")
        return
    
    action_reasoner = get_action_reasoner()
    
    print("\n" + "=" * 60)
    print("🎯 ActionReasoner 测试")
    print("=" * 60)
    
    # Test with a mock user context
    # In production, this would be loaded from the database
    test_user_id = 1
    
    print(f"\n📝 Testing plan generation for user_id={test_user_id}")
    
    try:
        # Generate plans
        plans = await action_reasoner.generate_plan(test_user_id)
        
        if plans:
            print(f"\n✅ Generated {len(plans)} action plan(s):")
            for i, plan in enumerate(plans, 1):
                print(f"\n--- Plan {i} ---")
                print(f"   Title: {plan.title}")
                print(f"   Category: {plan.category}")
                print(f"   Priority: {plan.priority}")
                print(f"   Confidence: {plan.confidence:.1%}")
                
                steps = plan.steps or []
                if steps:
                    print(f"   Steps ({len(steps)}):")
                    for step in steps[:3]:  # Show first 3 steps
                        action = step.get('action', 'N/A') if isinstance(step, dict) else str(step)
                        print(f"      - {action[:50]}...")
        else:
            print("\nℹ️ No plans generated (may need more user data)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ ActionReasoner test complete")
    print("=" * 60)


async def test_action_reasoner_with_sample_data():
    """Test ActionReasoner with sample asset data"""
    from app.services.action_reasoner import ActionReasoner
    from app.services.portfolio_analyzer import PortfolioAnalyzer
    from app.models.user import UserAsset, UserProfile, AssetType, RiskLevel
    
    print("\n" + "=" * 60)
    print("🧪 Testing with sample data")
    print("=" * 60)
    
    # Create sample assets
    sample_assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.REAL_ESTATE,
            name="北京望京自住房",
            value=5000000,
            extra_data={"usage": "self_occupied", "area": 90}
        ),
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金储蓄",
            value=200000,
            extra_data={}
        ),
        UserAsset(
            id=3,
            user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=2000000,
            extra_data={"monthly_payment": 12000}
        ),
    ]
    
    # Create sample profile
    sample_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="married_with_kids",
        risk_preference=RiskLevel.MODERATE
    )
    
    # Analyze portfolio
    analyzer = PortfolioAnalyzer()
    analysis = analyzer.analyze_portfolio(sample_assets, sample_profile)
    
    print(f"\n📊 Portfolio Analysis:")
    print(f"   Net Worth: ¥{analysis.net_worth:,.0f}")
    print(f"   Real Estate Ratio: {analysis.real_estate_ratio:.1%}")
    print(f"   Liquidity Ratio: {analysis.liquidity_ratio:.1f} months")
    print(f"   Risk Level: {analysis.overall_risk_level}")
    
    print(f"\n⚠️ Risk Warnings ({len(analysis.risk_warnings)}):")
    for warning in analysis.risk_warnings[:3]:
        print(f"   - [{warning['severity']}] {warning['title']}")
    
    print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
    for rec in analysis.recommendations[:3]:
        print(f"   - [{rec.get('priority', 'medium')}] {rec['title']}")


async def main():
    print(f"\n🚀 ActionReasoner 测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Basic ActionReasoner
    await test_action_reasoner()
    
    # Test 2: With sample data (includes PortfolioAnalyzer)
    await test_action_reasoner_with_sample_data()
    
    print("\n✅ All tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
