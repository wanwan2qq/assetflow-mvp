#!/usr/bin/env python3
"""
Test script to verify frontend parsing compatibility
"""

import json
import re
import sys
sys.path.append('.')

from app.services.ui_component_service import get_ui_component_service


def simulate_frontend_parsing(text):
    """Simulate the frontend _parseEmbeddedWidgets method"""
    widgets = []
    
    # Parse VALUATION_CARD with JSON data
    if '<WIDGET:VALUATION_CARD' in text:
        match = re.search(r'<WIDGET:VALUATION_CARD data="([^"]*)"', text)
        if match:
            try:
                json_str = match.group(1).replace('&quot;', '"').replace('\\"', '"')
                data = json.loads(json_str)
                widgets.append(('VALUATION_CARD', data))
                print(f"✅ VALUATION_CARD parsed: {data.get('location', 'N/A')} - {data.get('price', 0)/10000:.0f}万")
            except Exception as e:
                print(f"❌ VALUATION_CARD parsing error: {e}")
    
    # Parse ASSET_CARD with JSON data
    if '<WIDGET:ASSET_CARD' in text:
        match = re.search(r'<WIDGET:ASSET_CARD data="([^"]*)"', text)
        if match:
            try:
                json_str = match.group(1).replace('&quot;', '"')
                data = json.loads(json_str)
                widgets.append(('ASSET_CARD', data))
                print(f"✅ ASSET_CARD parsed: {data.get('name', 'N/A')} - {data.get('value', 0)/10000:.1f}万")
            except Exception as e:
                print(f"❌ ASSET_CARD parsing error: {e}")
    
    # Parse PRODUCT_CARD with JSON data
    if '<WIDGET:PRODUCT_CARD' in text:
        match = re.search(r'<WIDGET:PRODUCT_CARD data="([^"]*)"', text)
        if match:
            try:
                json_str = match.group(1).replace('&quot;', '"')
                data = json.loads(json_str)
                widgets.append(('PRODUCT_CARD', data))
                print(f"✅ PRODUCT_CARD parsed: {data.get('name', 'N/A')} by {data.get('provider', 'N/A')}")
            except Exception as e:
                print(f"❌ PRODUCT_CARD parsing error: {e}")
    
    # Parse ACTION_CARD with JSON data
    if '<WIDGET:ACTION_CARD' in text:
        matches = re.finditer(r'<WIDGET:ACTION_CARD data="([^"]*)"', text)
        for match in matches:
            try:
                json_str = match.group(1).replace('&quot;', '"')
                data = json.loads(json_str)
                widgets.append(('ACTION_CARD', data))
                print(f"✅ ACTION_CARD parsed: {data.get('title', 'N/A')} ({data.get('priority', 'medium')})")
            except Exception as e:
                print(f"❌ ACTION_CARD parsing error: {e}")
    
    # Parse PORTFOLIO_CHART with JSON data
    if '<WIDGET:PORTFOLIO_CHART' in text:
        match = re.search(r'<WIDGET:PORTFOLIO_CHART data="([^"]*)"', text)
        if match:
            try:
                json_str = match.group(1).replace('&quot;', '"')
                data = json.loads(json_str)
                widgets.append(('PORTFOLIO_CHART', data))
                assets_count = len(data.get('assets', []))
                total_value = data.get('total_value', 0)
                print(f"✅ PORTFOLIO_CHART parsed: {assets_count} assets, total {total_value/10000:.0f}万")
            except Exception as e:
                print(f"❌ PORTFOLIO_CHART parsing error: {e}")
    
    return widgets


def test_frontend_compatibility():
    """Test that backend-generated widgets can be parsed by frontend"""
    
    print("🧪 Testing Frontend Parsing Compatibility")
    print("=" * 50)
    
    ui_service = get_ui_component_service()
    
    # Generate a comprehensive set of widgets
    context = {
        'extracted_assets': [
            {
                'asset_type': 'real_estate',
                'name': '深圳南山房产',
                'value': 8000000,
                'location': '深圳南山',
                'area': 90
            },
            {
                'asset_type': 'cash',
                'name': '现金储蓄',
                'value': 500000
            }
        ],
        'portfolio_analysis': {
            'is_fresh': True,
            'risk_warnings': [
                {
                    'type': 'liquidity',
                    'title': '流动性风险提醒',
                    'recommendation': '建议增加现金储备',
                    'severity': 'high'
                }
            ]
        },
        'current_stage': 'analysis',
        'recommendations': [
            {
                'name': '平安保险重疾险',
                'provider': '平安保险',
                'category': 'insurance',
                'description': '全面保障重大疾病风险',
                'price': '年缴费5000元起',
                'roi': '保额50万',
                'buy_now_link': 'https://example.com/insurance',
                'product_info': True,
                'priority': 'high'
            }
        ],
        'newly_added_asset': {
            'name': '支付宝余额宝',
            'value': 80000,
            'asset_type': 'cash',
            'risk_level': 'low'
        },
    }
    
    # Generate widgets
    components = ui_service.generate_components_from_context(context)
    
    print(f"\n🔧 Backend generated {len(components)} components")
    
    # Simulate AI response with widgets
    ai_response = "根据您的资产情况，我为您生成了以下分析和建议：\n\n"
    for component in components:
        ai_response += f"\n{component}\n"
    
    print(f"\n📤 Simulated AI Response Length: {len(ai_response)} chars")
    
    # Test frontend parsing
    print(f"\n🔍 Frontend Parsing Results:")
    widgets = simulate_frontend_parsing(ai_response)
    
    print(f"\n📊 Summary:")
    print(f"  Backend generated: {len(components)} components")
    print(f"  Frontend parsed: {len(widgets)} widgets")
    
    if len(widgets) == len(components):
        print("✅ Perfect compatibility! All widgets parsed successfully.")
    else:
        print("⚠️  Parsing mismatch detected.")
    
    # Show widget types
    widget_types = [w[0] for w in widgets]
    print(f"  Widget types: {', '.join(widget_types)}")
    
    return len(widgets) == len(components)


if __name__ == "__main__":
    success = test_frontend_compatibility()
    if success:
        print("\n🎉 Frontend compatibility test PASSED!")
    else:
        print("\n❌ Frontend compatibility test FAILED!")
        sys.exit(1)