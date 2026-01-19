#!/usr/bin/env python3
"""
Test script to verify commercial product integration with card generation
"""

import asyncio
import sys
sys.path.append('.')

from app.services.ui_component_service import get_ui_component_service
from app.services.recommendation_service import get_recommendation_service


async def test_commercial_integration():
    """Test complete commercial product integration"""
    
    print("🧪 Testing Commercial Product Integration")
    print("=" * 50)
    
    ui_service = get_ui_component_service()
    rec_service = get_recommendation_service()
    
    # Step 1: Verify commercial products exist
    print("\n📊 Step 1: Verify Commercial Products")
    insurance_products = await rec_service.get_recommendations_by_category('insurance')
    investment_products = await rec_service.get_recommendations_by_category('investment')
    broker_products = await rec_service.get_recommendations_by_category('broker')
    
    print(f"  Insurance products: {len(insurance_products)}")
    print(f"  Investment products: {len(investment_products)}")
    print(f"  Broker products: {len(broker_products)}")
    
    if not (insurance_products or investment_products or broker_products):
        print("❌ No commercial products found! Run populate_commercial_products.py first.")
        return False
    
    # Step 2: Test recommendation generation
    print("\n🎯 Step 2: Test Recommendation Generation")
    risk_warnings = [
        {
            'type': 'liquidity',
            'title': '流动性不足',
            'recommendation': '建议增加现金储备至6个月生活费',
            'severity': 'high'
        },
        {
            'type': 'insurance',
            'title': '保险保障不足',
            'recommendation': '建议配置重疾险和意外险',
            'severity': 'medium'
        }
    ]
    
    recommendations = await rec_service.get_recommendations_for_risks(risk_warnings)
    print(f"  Generated {len(recommendations)} recommendations:")
    
    product_recommendations = []
    action_recommendations = []
    
    for rec in recommendations:
        if rec.get('buy_now_link'):
            product_recommendations.append(rec)
            print(f"    🛒 PRODUCT: {rec['name']} by {rec['provider']}")
        else:
            action_recommendations.append(rec)
            print(f"    ⚠️  ACTION: {rec['title']}")
    
    # Step 3: Test UI component generation
    print("\n🎨 Step 3: Test UI Component Generation")
    
    # Scenario: User with real estate + commercial recommendations
    context = {
        'extracted_assets': [
            {
                'asset_type': 'real_estate',
                'name': '深圳南山房产',
                'value': 12000000,
                'location': '深圳南山',
                'area': 100
            },
            {
                'asset_type': 'cash',
                'name': '现金储蓄',
                'value': 200000
            }
        ],
        'portfolio_analysis': {
            'is_fresh': True,
            'risk_warnings': risk_warnings
        },
        'current_stage': 'analysis',
        'recommendations': recommendations,
        'newly_added_asset': {
            'name': '新增基金投资',
            'value': 300000,
            'asset_type': 'investment',
            'risk_level': 'medium'
        },
    }
    
    components = ui_service.generate_components_from_context(context)
    print(f"  Generated {len(components)} UI components:")
    
    # Analyze component types
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
        print(f"    {comp_type}: {count}")
    
    # Step 4: Validate commercial integration
    print("\n✅ Step 4: Validation Results")
    
    success = True
    
    # Check PRODUCT_CARD generation
    if component_types.get('PRODUCT_CARD', 0) > 0:
        print("  ✅ PRODUCT_CARD generation: WORKING")
        print(f"     Generated {component_types['PRODUCT_CARD']} product cards with commercial data")
    else:
        print("  ❌ PRODUCT_CARD generation: FAILED")
        print("     No product cards generated despite having commercial products")
        success = False
    
    # Check ACTION_CARD generation
    if component_types.get('ACTION_CARD', 0) > 0:
        print("  ✅ ACTION_CARD generation: WORKING")
        print(f"     Generated {component_types['ACTION_CARD']} action cards from risk warnings")
    else:
        print("  ❌ ACTION_CARD generation: FAILED")
        success = False
    
    # Check VALUATION_CARD generation
    if component_types.get('VALUATION_CARD', 0) > 0:
        print("  ✅ VALUATION_CARD generation: WORKING")
    else:
        print("  ❌ VALUATION_CARD generation: FAILED")
        success = False
    
    # Check ASSET_CARD generation
    if component_types.get('ASSET_CARD', 0) > 0:
        print("  ✅ ASSET_CARD generation: WORKING")
    else:
        print("  ⚠️  ASSET_CARD generation: No new assets to display")
    
    # Step 5: Test frontend compatibility
    print("\n🔍 Step 5: Frontend Compatibility Check")
    
    # Simulate frontend parsing
    import re
    import json
    
    parsed_widgets = 0
    for comp in components:
        # Check if component has proper JSON data format
        if 'data="' in comp:
            match = re.search(r'data="([^"]*)"', comp)
            if match:
                try:
                    json_str = match.group(1).replace('&quot;', '"')
                    json.loads(json_str)
                    parsed_widgets += 1
                except json.JSONDecodeError:
                    print(f"    ❌ Invalid JSON in component: {comp[:50]}...")
                    success = False
    
    print(f"  Frontend parseable widgets: {parsed_widgets}/{len(components)}")
    if parsed_widgets == len(components):
        print("  ✅ All widgets have valid JSON data format")
    else:
        print("  ❌ Some widgets have invalid JSON format")
        success = False
    
    # Final result
    print(f"\n🎉 Overall Test Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("\n🚀 Commercial Integration Summary:")
        print("  • Commercial products successfully loaded into database")
        print("  • Recommendation service generating product suggestions")
        print("  • UI components include commercial PRODUCT_CARDs")
        print("  • Frontend-compatible JSON data format")
        print("  • Complete commercial loop: Risk → Product → Purchase Link")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(test_commercial_integration())
    if not success:
        sys.exit(1)