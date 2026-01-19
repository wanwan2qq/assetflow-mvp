#!/usr/bin/env python3
"""
Diagnose why recommendation cards are not showing for user 22
"""

import asyncio
import sys
sys.path.append('.')

from app.services.chat_agent import ChatAgent, ChatContext
from app.services.ui_component_service import get_ui_component_service
from app.services.recommendation_service import get_recommendation_service


async def diagnose_user_22_issue():
    """Diagnose recommendation issue for user 22"""
    
    print("🔍 Diagnosing Recommendation Issue for User 22")
    print("=" * 60)
    
    user_id = 22
    
    # Step 1: Check if user has data in database
    print("\n📊 Step 1: Check User Data in Database")
    try:
        from sqlmodel import select
        from app.core.database import get_db_session
        from app.models.user import User, UserProfile, UserAsset
        
        async for session in get_db_session():
            # Check user exists
            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            print(f"  User exists: {user is not None}")
            if user:
                print(f"  User phone: {user.phone}")
            
            # Check user profile
            profile_result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
            profile = profile_result.scalar_one_or_none()
            print(f"  User profile exists: {profile is not None}")
            if profile:
                print(f"  Age range: {profile.age_range}")
                print(f"  Family structure: {profile.family_structure}")
                print(f"  Monthly expense: {profile.monthly_expense}")
                print(f"  Risk preference: {profile.risk_preference}")
            
            # Check user assets
            assets_result = await session.execute(select(UserAsset).where(UserAsset.user_id == user_id))
            assets = assets_result.scalars().all()
            print(f"  User assets count: {len(assets)}")
            for asset in assets:
                print(f"    - {asset.asset_type.value}: {asset.name} = {asset.value}")
            
            break
            
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        return False
    
    # Step 2: Test recommendation service directly
    print("\n🎯 Step 2: Test Recommendation Service")
    rec_service = get_recommendation_service()
    
    # Test with simulated risk warnings
    risk_warnings = [
        {
            'type': 'liquidity',
            'title': '流动性不足',
            'recommendation': '建议增加现金储备',
            'severity': 'medium'
        },
        {
            'type': 'diversification',
            'title': '资产配置单一',
            'recommendation': '建议增加投资类资产',
            'severity': 'high'
        }
    ]
    
    try:
        recommendations = await rec_service.get_recommendations_for_risks(risk_warnings)
        print(f"  Generated recommendations: {len(recommendations)}")
        for i, rec in enumerate(recommendations):
            print(f"    {i+1}. {rec.get('name', 'N/A')} ({rec.get('category', 'N/A')})")
            print(f"       Has buy_now_link: {'buy_now_link' in rec}")
    except Exception as e:
        print(f"  ❌ Recommendation generation failed: {e}")
        return False
    
    # Step 3: Test UI component generation
    print("\n🎨 Step 3: Test UI Component Generation")
    ui_service = get_ui_component_service()
    
    # Create context similar to what the chat agent would have
    context_data = {
        'extracted_assets': [
            {
                'asset_type': 'real_estate',
                'name': '北京市海淀区房产',
                'value': 6000000,
                'location': '北京市海淀区',
                'area': 89.0
            },
            {
                'asset_type': 'cash',
                'name': '现金储蓄',
                'value': 500000
            }
        ],
        'portfolio_analysis': {
            'is_fresh': True,
            'risk_warnings': risk_warnings
        },
        'current_stage': 'analysis',
        'recommendations': recommendations,
        'newly_added_asset': None,
    }
    
    try:
        components = ui_service.generate_components_from_context(context_data)
        print(f"  Generated UI components: {len(components)}")
        
        component_types = {}
        for comp in components:
            if 'VALUATION_CARD' in comp:
                component_types['VALUATION_CARD'] = component_types.get('VALUATION_CARD', 0) + 1
            elif 'PRODUCT_CARD' in comp:
                component_types['PRODUCT_CARD'] = component_types.get('PRODUCT_CARD', 0) + 1
            elif 'ACTION_CARD' in comp:
                component_types['ACTION_CARD'] = component_types.get('ACTION_CARD', 0) + 1
            elif 'PORTFOLIO_CHART' in comp:
                component_types['PORTFOLIO_CHART'] = component_types.get('PORTFOLIO_CHART', 0) + 1
        
        for comp_type, count in component_types.items():
            print(f"    {comp_type}: {count}")
            
        # Show first few components
        print(f"\n  Sample components:")
        for i, comp in enumerate(components[:3]):
            widget_type = comp.split(':')[1].split(' ')[0].split('>')[0]
            print(f"    {i+1}. {widget_type}: {comp[:80]}...")
            
    except Exception as e:
        print(f"  ❌ UI component generation failed: {e}")
        return False
    
    # Step 4: Test chat agent integration
    print("\n🤖 Step 4: Test Chat Agent Integration")
    
    try:
        chat_agent = ChatAgent()
        
        # Create a context similar to what would be in a real conversation
        context = ChatContext(
            user_id=user_id,
            extracted_assets=context_data['extracted_assets'],
            current_stage='analysis'
        )
        context.portfolio_analysis = context_data['portfolio_analysis']
        
        # Test the UI enhancement method
        test_response = "基于您的资产配置分析，我发现了一些需要关注的风险点。"
        
        enhanced_response = await chat_agent._enhance_response_with_ui_components(
            test_response, context, user_id
        )
        
        print(f"  Original response length: {len(test_response)}")
        print(f"  Enhanced response length: {len(enhanced_response)}")
        print(f"  Components added: {len(enhanced_response) > len(test_response)}")
        
        if len(enhanced_response) > len(test_response):
            # Count widgets in enhanced response
            widget_count = enhanced_response.count('<WIDGET:')
            print(f"  Widget tags found: {widget_count}")
        
    except Exception as e:
        print(f"  ❌ Chat agent integration failed: {e}")
        return False
    
    # Step 5: Provide debugging recommendations
    print(f"\n💡 Debugging Recommendations")
    print("=" * 60)
    
    if len(components) == 0:
        print("❌ No UI components generated - check recommendation service")
    elif 'PRODUCT_CARD' not in component_types:
        print("❌ No PRODUCT_CARD generated - check commercial products")
    else:
        print("✅ UI components generated successfully")
        print("🔍 Issue might be in:")
        print("  1. Chat agent not calling UI enhancement")
        print("  2. Frontend not parsing the widget tags")
        print("  3. WebSocket message truncation")
    
    print(f"\n🔧 Next Steps:")
    print("1. Check backend logs for UI component generation")
    print("2. Check WebSocket messages in browser console")
    print("3. Verify frontend widget parsing logic")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(diagnose_user_22_issue())
    if success:
        print("\n✅ Diagnosis completed!")
    else:
        print("\n❌ Diagnosis failed!")
        sys.exit(1)