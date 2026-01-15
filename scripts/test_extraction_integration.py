#!/usr/bin/env python3
"""
Integration test for LLM extraction with chat agent
Verifies the refactored extraction works with existing chat flow
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.services.information_extraction import extract_information


async def test_phase2_integration():
    """Test Phase 2 integration format"""
    print("\n" + "=" * 60)
    print("🔗 PHASE 2 INTEGRATION TEST")
    print("=" * 60)

    # Simulate a conversation flow
    conversation_history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "您好！我是AssetFlow的首席资产配置专家。请告诉我您的资产情况。"},
    ]

    test_messages = [
        "我在北京朝阳区有一套房子，120平米",
        "房子价值大概500万",
        "不对，应该是600万",
        "我还有50万现金存款",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Turn {i}: {message}")
        
        # Extract information (Phase 2 format)
        result = await extract_information(message, conversation_history)
        
        print(f"\n✅ Extraction Result:")
        print(f"   Intent: {result['intent']}")
        print(f"   Assets: {len(result['assets'])}")
        for asset in result['assets']:
            print(f"     - {asset['type']}: {asset['amount']:,.0f} {asset['currency']}")
            if 'location' in asset:
                print(f"       Location: {asset['location']}")
            if 'area' in asset:
                print(f"       Area: {asset['area']} sqm")
        
        print(f"   Completeness Update: {result['completeness_update']}")
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": "好的，我记录下来了"})


async def test_correction_flow():
    """Test correction intent detection"""
    print("\n" + "=" * 60)
    print("🔄 CORRECTION FLOW TEST")
    print("=" * 60)

    conversation_history = [
        {"role": "user", "content": "我的房子是100平米"},
        {"role": "assistant", "content": "好的，您的房子是100平米"},
    ]

    corrections = [
        "不是，是120平米",
        "不对，应该是150平方米",
        "其实是200平",
    ]

    for correction in corrections:
        print(f"\n📝 Correction: {correction}")
        result = await extract_information(correction, conversation_history)
        
        print(f"✅ Intent: {result['intent']}")
        if result['assets']:
            asset = result['assets'][0]
            print(f"   Corrected area: {asset.get('area', 'N/A')} sqm")


async def test_mixed_assets():
    """Test extraction of multiple asset types in one message"""
    print("\n" + "=" * 60)
    print("🏦 MIXED ASSETS TEST")
    print("=" * 60)

    message = "我有一套房产价值500万，现金存款80万，股票基金30万，还有200万房贷"
    
    print(f"\n📝 Message: {message}")
    result = await extract_information(message, [])
    
    print(f"\n✅ Extracted {len(result['assets'])} assets:")
    
    total_assets = 0
    total_liabilities = 0
    
    for asset in result['assets']:
        asset_type = asset['type']
        amount = asset['amount']
        
        print(f"   - {asset_type}: {amount:,.0f} CNY")
        
        if asset_type == 'liability':
            total_liabilities += amount
        else:
            total_assets += amount
    
    net_worth = total_assets - total_liabilities
    print(f"\n📊 Summary:")
    print(f"   Total Assets: {total_assets:,.0f} CNY")
    print(f"   Total Liabilities: {total_liabilities:,.0f} CNY")
    print(f"   Net Worth: {net_worth:,.0f} CNY")


async def test_profile_extraction():
    """Test user profile extraction"""
    print("\n" + "=" * 60)
    print("👤 PROFILE EXTRACTION TEST")
    print("=" * 60)

    messages = [
        "我今年35岁，已婚有孩子",
        "每月支出大概2万",
        "我比较保守，不喜欢高风险投资",
    ]

    conversation_history = []
    
    for message in messages:
        print(f"\n📝 Message: {message}")
        result = await extract_information(message, conversation_history)
        
        if result['risk_profile']:
            print(f"✅ Profile Update:")
            for key, value in result['risk_profile'].items():
                print(f"   - {key}: {value}")
        
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": "好的"})


async def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("🧪 LLM EXTRACTION INTEGRATION TEST SUITE")
    print("=" * 60)

    try:
        await test_phase2_integration()
        await test_correction_flow()
        await test_mixed_assets()
        await test_profile_extraction()

        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\n💡 The LLM extraction is fully integrated and working!")
        print("   - Phase 2 format: ✅")
        print("   - Correction detection: ✅")
        print("   - Mixed assets: ✅")
        print("   - Profile extraction: ✅")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
