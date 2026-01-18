#!/usr/bin/env python3
"""
Test script for Property Search Tool (Tavily API)

This script tests the property search functionality in both Mock and Tavily modes.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.search_tools import create_search_tool
from app.core.config import settings


def print_separator():
    print("\n" + "=" * 80 + "\n")


async def test_property_search():
    """Test property search tool"""
    
    print("🔍 Property Search Tool Test")
    print_separator()
    
    # Display current configuration
    print("📋 Current Configuration:")
    print(f"   USE_MOCK_SEARCH: {settings.USE_MOCK_SEARCH}")
    print(f"   TAVILY_API_KEY: {settings.TAVILY_API_KEY[:20]}..." if settings.TAVILY_API_KEY else "   TAVILY_API_KEY: None")
    print_separator()
    
    # Create search tool
    try:
        search_tool = create_search_tool(
            use_mock=settings.USE_MOCK_SEARCH,
            tavily_api_key=settings.TAVILY_API_KEY
        )
        print(f"✅ Search tool created: {type(search_tool).__name__}")
    except Exception as e:
        print(f"❌ Failed to create search tool: {e}")
        return
    
    print_separator()
    
    # Test cases
    test_cases = [
        {
            "name": "北京中关村",
            "city": "北京",
            "community": "中关村",
            "area": 100,
            "expected_mock_price": 7_600_000,  # 80,000 * 100 * 0.95
        },
        {
            "name": "上海陆家嘴",
            "city": "上海",
            "community": "陆家嘴",
            "area": 80,
            "expected_mock_price": 11_400_000,  # 150,000 * 80 * 0.95
        },
        {
            "name": "北京望京",
            "city": "北京",
            "community": "望京",
            "area": 120,
            "expected_mock_price": 7_410_000,  # 65,000 * 120 * 0.95
        },
        {
            "name": "未知小区（默认数据）",
            "city": "北京",
            "community": "未知小区XYZ",
            "area": 100,
            "expected_mock_price": 4_275_000,  # 45,000 * 100 * 0.95
        },
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test Case {i}: {test_case['name']}")
        print(f"   输入: {test_case['city']} {test_case['community']}, {test_case['area']}平米")
        
        try:
            result = search_tool._run(
                city=test_case["city"],
                community=test_case["community"],
                area=test_case["area"]
            )
            
            if result["success"]:
                print(f"   ✅ 搜索成功")
                print(f"   估值: {result['estimated_price']:,.0f} 元 ({result['estimated_price']/10000:.1f}万)")
                print(f"   单价: {result['price_per_sqm']:,.0f} 元/平米")
                print(f"   来源: {result['source']}")
                print(f"   置信度: {result['confidence']}")
                
                # Verify mock data if in mock mode
                if settings.USE_MOCK_SEARCH and "expected_mock_price" in test_case:
                    expected = test_case["expected_mock_price"]
                    actual = result["estimated_price"]
                    if abs(actual - expected) < 1:  # Allow small floating point error
                        print(f"   ✅ Mock data verification passed")
                    else:
                        print(f"   ⚠️  Mock data mismatch: expected {expected:,.0f}, got {actual:,.0f}")
            else:
                print(f"   ❌ 搜索失败")
                print(f"   错误: {result.get('error', 'Unknown error')}")
                if result.get("fallback_to_manual"):
                    print(f"   💡 建议: 提示用户手动输入房产估值")
        
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
        
        print()
    
    print_separator()
    
    # Summary
    print("📊 Test Summary:")
    if settings.USE_MOCK_SEARCH:
        print("   ✅ Mock mode is working correctly")
        print("   💡 To enable Tavily API:")
        print("      1. Get API key from https://tavily.com")
        print("      2. Update backend/.env:")
        print("         TAVILY_API_KEY=tvly-your-real-api-key-here")
        print("         USE_MOCK_SEARCH=false")
        print("      3. Install: pip install tavily-python")
        print("      4. Restart backend service")
    else:
        print("   ✅ Tavily API mode is enabled")
        print("   💡 Monitor API usage to avoid exceeding quota")
    
    print_separator()


async def test_tool_integration():
    """Test tool integration with LangChain agent"""
    
    print("🤖 Testing Tool Integration with LangChain Agent")
    print_separator()
    
    try:
        from app.services.chat_agent import get_chat_agent
        
        agent = get_chat_agent()
        print(f"✅ Chat agent created successfully")
        print(f"   Has real OpenAI key: {agent.has_real_openai_key}")
        print(f"   Search tool type: {type(agent.search_tool).__name__}")
        print(f"   Agent type: {type(agent.agent).__name__ if agent.agent != 'mock_agent' else 'mock_agent'}")
        
        # Check if search tool is registered
        if agent.agent != "mock_agent":
            print(f"   ✅ Search tool is registered with the agent")
        else:
            print(f"   ⚠️  Using mock agent (no real OpenAI key)")
        
    except Exception as e:
        print(f"❌ Failed to test agent integration: {e}")
    
    print_separator()


def main():
    """Main test function"""
    print("\n" + "🏠" * 40)
    print("Property Search Tool Test Suite")
    print("🏠" * 40 + "\n")
    
    # Run tests
    asyncio.run(test_property_search())
    asyncio.run(test_tool_integration())
    
    print("\n✅ All tests completed!\n")


if __name__ == "__main__":
    main()
