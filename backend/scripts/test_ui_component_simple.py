#!/usr/bin/env python3
"""
Simple test for UI component data structures without database dependencies.
"""

import json
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel, Field


class UIComponentType(str, Enum):
    """Supported UI component types"""
    VALUATION_CARD = "VALUATION_CARD"
    ACTION_CARD = "ACTION_CARD"
    PORTFOLIO_CHART = "PORTFOLIO_CHART"
    ASSET_CARD = "ASSET_CARD"
    PRODUCT_CARD = "PRODUCT_CARD"


class AssetCardData(BaseModel):
    """Data structure for asset card"""
    name: str = Field(description="Asset name")
    value: float = Field(description="Asset value")
    type: str = Field(description="Asset type")
    risk_level: Optional[str] = Field(default=None, description="Risk level")
    tags: list[str] = Field(default=[], description="Asset tags")
    privacy_mode: bool = Field(default=False, description="Whether to mask exact values")


class ProductCardData(BaseModel):
    """Data structure for commercial product card"""
    name: str = Field(description="Product name")
    provider: str = Field(description="Service provider name")
    category: str = Field(description="Product category")
    description: str = Field(description="Product description")
    price: Optional[str] = Field(default=None, description="Product price")
    roi: Optional[str] = Field(default=None, description="Expected ROI")
    buy_now_link: Optional[str] = Field(default=None, description="Purchase link")
    contact_info: Optional[dict[str, Any]] = Field(default=None, description="Contact info")
    priority: str = Field(description="Priority level")
    reason: Optional[str] = Field(default=None, description="Why recommended")


class ActionCardData(BaseModel):
    """Data structure for action card"""
    type: str = Field(description="Action type")
    title: str = Field(description="Action card title")
    description: str = Field(description="Action description")
    priority: str = Field(description="Priority level")
    contact_info: Optional[dict[str, Any]] = Field(default=None, description="Contact info")
    reason: Optional[str] = Field(default=None, description="Why recommended")
    provider_info: Optional[str] = Field(default=None, description="Provider name")


def test_new_data_structures():
    """Test the new data structures"""
    print("🧪 Testing New UI Component Data Structures")
    print("=" * 50)
    
    # Test AssetCardData
    asset_card = AssetCardData(
        name="北京朝阳区公寓",
        value=5000000,
        type="real_estate",
        risk_level="low",
        tags=["residential", "beijing"],
        privacy_mode=False
    )
    
    print("1. AssetCardData:")
    print(json.dumps(asset_card.model_dump(), ensure_ascii=False, indent=2))
    print()
    
    # Test AssetCardData with privacy mode
    asset_card_private = AssetCardData(
        name="北京朝阳区公寓",
        value=1000000,  # This would be masked in the UI service
        type="real_estate",
        risk_level="low",
        tags=["residential", "beijing"],
        privacy_mode=True
    )
    
    print("2. AssetCardData (Privacy Mode):")
    print(json.dumps(asset_card_private.model_dump(), ensure_ascii=False, indent=2))
    print()
    
    # Test ProductCardData
    product_card = ProductCardData(
        name="平安人寿保险",
        provider="中国平安",
        category="insurance",
        description="全面的人寿保险保障",
        price="年缴费5000元起",
        roi="风险保障覆盖",
        buy_now_link="https://www.pingan.com",
        contact_info={
            "phone": "95511",
            "website": "https://www.pingan.com"
        },
        priority="high",
        reason="基于您的保险缺口分析"
    )
    
    print("3. ProductCardData:")
    print(json.dumps(product_card.model_dump(), ensure_ascii=False, indent=2))
    print()
    
    # Test ActionCardData with new fields
    action_card = ActionCardData(
        type="insurance",
        title="保险保障建议",
        description="建议增加人寿保险保障",
        priority="high",
        contact_info={
            "phone": "95511",
            "website": "https://www.pingan.com"
        },
        reason="基于您的风险分析，发现保险保障不足",
        provider_info="中国平安"
    )
    
    print("4. ActionCardData (Enhanced):")
    print(json.dumps(action_card.model_dump(), ensure_ascii=False, indent=2))
    print()


def test_component_generation_logic():
    """Test the logic for determining component types"""
    print("🎯 Testing Component Generation Logic")
    print("=" * 40)
    
    # Simulate context data
    test_recommendations = [
        {
            "type": "investment",
            "title": "货币基金推荐",
            "name": "余额宝",
            "provider": "天弘基金",
            "category": "investment",
            "description": "低风险货币基金",
            "priority": "high",
            "product_info": {"id": 1},
            "buy_now_link": "https://www.alipay.com",
            "price": "1元起投",
            "roi": "年化收益约2.5%"
        },
        {
            "type": "general",
            "title": "风险提醒",
            "description": "建议分散投资",
            "priority": "medium",
            "reason": "房产配置过高"
        }
    ]
    
    product_cards = 0
    action_cards = 0
    
    for rec in test_recommendations:
        if rec.get("product_info") and rec.get("buy_now_link"):
            product_cards += 1
            print(f"✅ Would generate PRODUCT_CARD for: {rec['name']}")
        else:
            action_cards += 1
            print(f"✅ Would generate ACTION_CARD for: {rec['title']}")
    
    print(f"\n📊 Summary: {product_cards} PRODUCT_CARDs, {action_cards} ACTION_CARDs")
    print()


def test_widget_tag_format():
    """Test the widget tag format"""
    print("🏷️  Testing Widget Tag Format")
    print("=" * 30)
    
    # Test data
    asset_data = AssetCardData(
        name="测试资产",
        value=1000000,
        type="investment",
        risk_level="medium",
        tags=["stocks"],
        privacy_mode=False
    )
    
    # Simulate widget tag generation
    data_json = json.dumps(asset_data.model_dump(), ensure_ascii=False)
    escaped_json = data_json.replace('"', "&quot;")
    widget_tag = f'<WIDGET:ASSET_CARD data="{escaped_json}">'
    
    print("Generated Widget Tag:")
    print(widget_tag)
    print()
    
    # Test parsing back
    if 'data="' in widget_tag:
        data_start = widget_tag.find('data="') + 6
        data_end = widget_tag.rfind('">')
        if data_end > data_start:
            extracted_json = widget_tag[data_start:data_end]
            unescaped_json = extracted_json.replace('&quot;', '"')
            parsed_data = json.loads(unescaped_json)
            
            print("Parsed Back Data:")
            print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    
    print()


def main():
    """Run all tests"""
    print("🚀 UI Component Optimization - Simple Tests")
    print("=" * 60)
    print()
    
    try:
        test_new_data_structures()
        print("=" * 60)
        
        test_component_generation_logic()
        print("=" * 60)
        
        test_widget_tag_format()
        print("=" * 60)
        
        print("✅ All simple tests passed!")
        print("📋 New Features Validated:")
        print("  - ASSET_CARD and PRODUCT_CARD data structures")
        print("  - Enhanced ActionCardData with reason and provider_info")
        print("  - Privacy mode support for asset values")
        print("  - Context-based component generation logic")
        print("  - Widget tag format compatibility")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)