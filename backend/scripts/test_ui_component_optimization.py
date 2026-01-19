#!/usr/bin/env python3
"""
Test script for the optimized UIComponentService and ChatAgent integration.
Tests the new context-based component generation approach.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.ui_component_service import UIComponentService
from app.models.user import AssetType


async def test_context_based_component_generation():
    """Test the new generate_components_from_context method"""
    print("🧪 Testing Context-Based UI Component Generation")
    print("=" * 60)
    
    ui_service = UIComponentService()
    
    # Test data simulating a chat context with portfolio analysis
    test_context = {
        "extracted_assets": [
            {
                "name": "北京朝阳区公寓",
                "value": 5000000,
                "asset_type": "real_estate",
                "risk_level": "low",
                "tags": ["residential", "beijing"]
            },
            {
                "name": "股票投资",
                "value": 1000000,
                "asset_type": "investment",
                "risk_level": "high",
                "tags": ["stocks", "equity"]
            },
            {
                "name": "银行存款",
                "value": 500000,
                "asset_type": "cash",
                "risk_level": "low",
                "tags": ["savings", "liquid"]
            }
        ],
        "portfolio_analysis": {
            "is_fresh": True,
            "risk_warnings": [
                {
                    "type": "HIGH_RE_CONCENTRATION",
                    "title": "房产配置过高",
                    "description": "房产占比超过75%，存在流动性风险",
                    "recommendation": "建议增加流动性资产配置",
                    "severity": "high"
                },
                {
                    "type": "LIQUIDITY_CRISIS",
                    "title": "流动性不足",
                    "description": "现金及等价物不足3个月支出",
                    "recommendation": "建议增加货币基金或短期理财",
                    "severity": "medium"
                }
            ]
        },
        "recommendations": [
            {
                "type": "investment",
                "title": "货币基金推荐",
                "name": "余额宝",
                "provider": "天弘基金",
                "category": "investment",
                "description": "低风险货币基金，随存随取",
                "priority": "high",
                "reason": "提高资产流动性",
                "product_info": {
                    "id": 1,
                    "name": "余额宝",
                    "provider": "天弘基金",
                    "category": "investment"
                },
                "buy_now_link": "https://www.alipay.com",
                "price": "1元起投",
                "roi": "年化收益约2.5%",
                "contact_info": {
                    "website": "https://www.alipay.com",
                    "phone": "95188"
                }
            }
        ],
        "newly_added_asset": {
            "name": "新增保险",
            "value": 100000,
            "asset_type": "insurance",
            "risk_level": "low",
            "tags": ["life_insurance", "protection"]
        },
        "current_stage": "analysis"
    }
    
    # Test user profile
    test_user_profile = {
        "age_range": "30-40",
        "family_structure": "married_with_kids",
        "risk_preference": "moderate"
    }
    
    print("📊 Test Context:")
    print(f"  - Assets: {len(test_context['extracted_assets'])}")
    print(f"  - Risk Warnings: {len(test_context['portfolio_analysis']['risk_warnings'])}")
    print(f"  - Recommendations: {len(test_context['recommendations'])}")
    print(f"  - Newly Added Asset: {test_context['newly_added_asset']['name']}")
    print()
    
    # Generate components using the new context-based approach
    components = ui_service.generate_components_from_context(
        test_context, 
        test_user_profile, 
        privacy_mode=False
    )
    
    print(f"✅ Generated {len(components)} UI Components:")
    print("-" * 40)
    
    for i, component in enumerate(components, 1):
        # Extract component type from the widget tag
        if '<WIDGET:' in component:
            widget_type = component.split('<WIDGET:')[1].split(' ')[0].split('>')[0]
            print(f"{i}. {widget_type}")
            
            # Extract and pretty print the data
            if 'data="' in component:
                data_start = component.find('data="') + 6
                data_end = component.rfind('">')
                if data_end > data_start:
                    escaped_json = component[data_start:data_end]
                    # Unescape the JSON
                    json_str = escaped_json.replace('&quot;', '"')
                    try:
                        data = json.loads(json_str)
                        print(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"   Raw data: {escaped_json[:100]}...")
        else:
            print(f"{i}. Unknown component format")
        print()
    
    return components


async def test_asset_card_privacy_mode():
    """Test asset card generation with privacy mode"""
    print("🔒 Testing Asset Card Privacy Mode")
    print("=" * 40)
    
    ui_service = UIComponentService()
    
    # Test with privacy mode off
    normal_card = ui_service.generate_asset_card(
        name="北京房产",
        value=5500000,
        asset_type="real_estate",
        risk_level="low",
        tags=["residential", "beijing"],
        privacy_mode=False
    )
    
    # Test with privacy mode on
    private_card = ui_service.generate_asset_card(
        name="北京房产",
        value=5500000,
        asset_type="real_estate",
        risk_level="low",
        tags=["residential", "beijing"],
        privacy_mode=True
    )
    
    print("Normal Mode (exact values):")
    print(normal_card)
    print()
    print("Privacy Mode (masked values):")
    print(private_card)
    print()


async def test_product_card_generation():
    """Test commercial product card generation"""
    print("💳 Testing Product Card Generation")
    print("=" * 40)
    
    ui_service = UIComponentService()
    
    product_card = ui_service.generate_product_card(
        name="平安人寿保险",
        provider="中国平安",
        category="insurance",
        description="全面的人寿保险保障，覆盖意外、疾病、身故等风险",
        priority="high",
        price="年缴费5000元起",
        roi="风险保障覆盖",
        buy_now_link="https://www.pingan.com",
        contact_info={
            "phone": "95511",
            "website": "https://www.pingan.com",
            "address": "深圳市福田区"
        },
        reason="基于您的保险缺口分析"
    )
    
    print("Generated Product Card:")
    print(product_card)
    print()


async def main():
    """Run all tests"""
    print("🚀 UI Component Service Optimization Tests")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Context-based component generation
        components = await test_context_based_component_generation()
        
        print()
        print("=" * 60)
        
        # Test 2: Privacy mode
        await test_asset_card_privacy_mode()
        
        print("=" * 60)
        
        # Test 3: Product card generation
        await test_product_card_generation()
        
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print(f"📈 Summary: Generated {len(components)} components from context")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)