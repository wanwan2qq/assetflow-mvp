#!/usr/bin/env python3
"""
Test script to verify recommendation card triggering
"""

import asyncio
import sys
sys.path.append('.')

from app.services.chat_agent import ChatAgent, ChatContext
from app.services.ui_component_service import get_ui_component_service


async def test_recommendation_trigger():
    """Test the complete recommendation triggering flow"""
    
    print("🧪 Testing Recommendation Card Triggering")
    print("=" * 50)
    
    # Create a chat agent (using mock mode for testing)
    chat_agent = ChatAgent()
    ui_service = get_ui_component_service()
    
    # Simulate a user context with complete information
    user_id = 22  # Your user ID from the logs
    
    # Create context with user information and assets
    context = ChatContext(
        user_id=user_id,
        extracted_assets=[
            {
                'asset_type': 'real_estate',
                'name': '北京市海淀区房产',
                'value': 6000000,
                'location': '北京市海淀区',
                'area': 89.0,
                'confidence': 0.7
            },
            {
                'asset_type': 'cash',
                'name': '现金储蓄',
                'value': 500000,
                'confidence': 0.8
            }
        ],
        user_profile={
            'age_range': '30-40',
            'family_structure': 'married_with_kids',
            'monthly_expense': 20000,
            'risk_preference': 'moderate',
            'income_range': '50-100万'
        },
        current_stage='analysis'
    )
    
    # Simulate portfolio analysis with risk warnings
    context.portfolio_analysis = {
        'is_fresh': True,
        'risk_warnings': [
            {
                'type': 'liquidity',
                'title': '流动性不足',
                'recommendation': '建议增加现金储备至6个月生活费',
                'severity': 'medium',
                'description': '当前现金储备仅占总资产7.7%，低于建议的10-20%'
            },
            {
                'type': 'diversification',
                'title': '资产配置单一',
                'recommendation': '建议增加投资类资产配置',
                'severity': 'high',
                'description': '房产占比过高，缺乏多元化投资'
            }
        ]
    }
    
    # Test UI component generation
    print("\n🎨 Testing UI Component Generation")
    
    # Get recommendations from risk warnings
    from app.services.recommendation_service import get_recommendation_service
    rec_service = get_recommendation_service()
    
    recommendations = await rec_service.get_recommendations_for_risks(
        context.portfolio_analysis['risk_warnings'],
        user_profile=None,  # Will use default matching
        limit=5
    )
    
    print(f"📊 Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations):
        print(f"  {i+1}. {rec.get('name', 'N/A')} by {rec.get('provider', 'N/A')}")
        print(f"     Category: {rec.get('category', 'N/A')}")
        print(f"     Has buy_now_link: {'buy_now_link' in rec}")
    
    # Create context with recommendations
    context_data = {
        'extracted_assets': context.extracted_assets,
        'portfolio_analysis': context.portfolio_analysis,
        'current_stage': context.current_stage,
        'recommendations': recommendations,
        'newly_added_asset': None,
    }
    
    # Generate UI components
    components = ui_service.generate_components_from_context(context_data)
    
    print(f"\n🎯 Generated {len(components)} UI components:")
    
    component_types = {}
    for comp in components:
        if 'VALUATION_CARD' in comp:
            component_types['VALUATION_CARD'] = component_types.get('VALUATION_CARD', 0) + 1
        elif 'PRODUCT_CARD' in comp:
            component_types['PRODUCT_CARD'] = component_types.get('PRODUCT_CARD', 0) + 1
        elif 'ACTION_CARD' in comp:
            component_types['ACTION_CARD'] = component_types.get('ACTION_CARD', 0) + 1
        elif 'ASSET_CARD' in comp:
            component_types['ASSET_CARD'] = component_types.get('ASSET_CARD', 0) + 1
        elif 'PORTFOLIO_CHART' in comp:
            component_types['PORTFOLIO_CHART'] = component_types.get('PORTFOLIO_CHART', 0) + 1
    
    for comp_type, count in component_types.items():
        print(f"  {comp_type}: {count}")
    
    # Show what the AI response would look like
    print(f"\n📝 Sample AI Response with Components:")
    ai_response = """基于您的资产情况分析，我发现以下几个需要关注的问题：

1. **流动性不足**: 您的现金储备仅占总资产的7.7%，建议增加到10-20%
2. **资产配置单一**: 房产占比过高，建议增加多元化投资

针对这些问题，我为您推荐以下解决方案："""
    
    # Add components to response
    for component in components:
        ai_response += f"\n\n{component}"
    
    print(ai_response[:500] + "..." if len(ai_response) > 500 else ai_response)
    
    # Provide user guidance
    print(f"\n💡 要在实际聊天中触发推荐卡片，请输入：")
    print("=" * 50)
    print("1. 我今年35岁，已婚，有一个孩子，产品经理，家庭年收入100万")
    print("2. 除了房产，我还有现金储蓄50万，没有其他投资")
    print("3. 请帮我分析资产配置并给出投资建议")
    print("=" * 50)
    
    return len(components) > 0


if __name__ == "__main__":
    success = asyncio.run(test_recommendation_trigger())
    if success:
        print("\n✅ 推荐系统测试成功！")
    else:
        print("\n❌ 推荐系统测试失败！")
        sys.exit(1)