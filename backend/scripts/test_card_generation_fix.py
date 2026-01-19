#!/usr/bin/env python3
"""
Test script to verify the card generation fix
"""

import asyncio
import sys
sys.path.append('.')

from app.services.ui_component_service import get_ui_component_service
from app.services.chat_agent import ChatAgent, ChatContext


async def test_card_generation_scenarios():
    """Test different scenarios for card generation"""
    
    print("🧪 Testing Card Generation Fix")
    print("=" * 50)
    
    ui_service = get_ui_component_service()
    
    # Scenario 1: User with real estate only (should show VALUATION_CARD)
    print("\n📋 Scenario 1: Real Estate Only")
    context1 = {
        'extracted_assets': [
            {
                'asset_type': 'real_estate',
                'name': '北京天通苑',
                'value': 4500000,
                'location': '北京天通苑',
                'area': 120
            }
        ],
        'portfolio_analysis': None,
        'current_stage': 'analysis',
        'recommendations': [],
        'newly_added_asset': None,
    }
    
    components1 = ui_service.generate_components_from_context(context1)
    print(f"✅ Generated {len(components1)} components:")
    for i, comp in enumerate(components1):
        widget_type = comp.split(':')[1].split(' ')[0].split('>')[0]
        print(f"  {i+1}. {widget_type}")
    
    # Scenario 2: User with multiple assets + recommendations (should show multiple cards)
    print("\n📋 Scenario 2: Multiple Assets + Recommendations")
    context2 = {
        'extracted_assets': [
            {
                'asset_type': 'real_estate',
                'name': '上海房产',
                'value': 6000000,
                'location': '上海浦东',
                'area': 100
            },
            {
                'asset_type': 'cash',
                'name': '现金储蓄',
                'value': 300000
            }
        ],
        'portfolio_analysis': {
            'is_fresh': True,
            'risk_warnings': [
                {
                    'type': 'liquidity',
                    'title': '流动性不足',
                    'recommendation': '建议增加现金储备至6个月生活费',
                    'severity': 'medium'
                }
            ]
        },
        'current_stage': 'analysis',
        'recommendations': [
            {
                'type': 'insurance',
                'title': '保险保障建议',
                'description': '建议配置重疾险和意外险',
                'priority': 'high'
            },
            {
                'name': '招商银行理财产品',
                'provider': '招商银行',
                'category': 'investment',
                'description': '稳健型理财产品，年化收益4.5%',
                'price': '起购金额1万元',
                'roi': '年化4.5%',
                'buy_now_link': 'https://example.com/product',
                'product_info': True,
                'priority': 'medium'
            }
        ],
        'newly_added_asset': {
            'name': '新增基金投资',
            'value': 150000,
            'asset_type': 'investment',
            'risk_level': 'medium'
        },
    }
    
    components2 = ui_service.generate_components_from_context(context2)
    print(f"✅ Generated {len(components2)} components:")
    for i, comp in enumerate(components2):
        widget_type = comp.split(':')[1].split(' ')[0].split('>')[0]
        print(f"  {i+1}. {widget_type}")
    
    # Scenario 3: Test legacy fallback (empty context)
    print("\n📋 Scenario 3: Empty Context (Legacy Fallback)")
    context3 = {
        'extracted_assets': [],
        'portfolio_analysis': None,
        'current_stage': 'initial',
        'recommendations': [],
        'newly_added_asset': None,
    }
    
    components3 = ui_service.generate_components_from_context(context3)
    print(f"✅ Generated {len(components3)} components (should be 0):")
    
    # Test legacy methods separately
    response = "根据您的情况，我建议增加保险保障"
    should_action = ui_service.should_generate_action_cards(response, 'analysis')
    print(f"🔍 Legacy should_generate_action_cards: {should_action}")
    
    print("\n🎉 Card Generation Fix Test Complete!")
    print("Expected behavior:")
    print("- Scenario 1: 1 VALUATION_CARD")
    print("- Scenario 2: 5 cards (VALUATION_CARD + PORTFOLIO_CHART + 2 ACTION_CARDs + 1 ASSET_CARD + 1 PRODUCT_CARD)")
    print("- Scenario 3: 0 cards (empty context)")


if __name__ == "__main__":
    asyncio.run(test_card_generation_scenarios())