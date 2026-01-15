#!/usr/bin/env python3
"""
Test script for LLM-based information extraction
Tests the refactored InformationExtractor with various scenarios
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

from app.services.information_extraction import (
    information_extractor,
    extract_information,
)


async def test_real_estate_extraction():
    """Test real estate extraction with location and area"""
    print("\n" + "=" * 60)
    print("TEST 1: Real Estate Extraction")
    print("=" * 60)

    test_cases = [
        "我在北京朝阳区有一套房子，大概120平米，价值500万",
        "我有一套天通苑的房产，面积100平方米",
        "上海浦东的房子，150平，大概值800万",
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {message}")
        assets, profile, validation = await information_extractor.extract_information_from_conversation(
            message
        )

        print(f"\n✅ Extracted {len(assets)} asset(s):")
        for asset in assets:
            print(f"  - Type: {asset.asset_type.value}")
            print(f"    Name: {asset.name}")
            print(f"    Value: {asset.value}")
            print(f"    Location: {asset.location}")
            print(f"    Area: {asset.area}")
            print(f"    Confidence: {asset.confidence}")

        print(f"\n📊 Validation:")
        print(f"  - Valid: {validation['is_valid']}")
        print(f"  - Completeness: {validation['completeness_score']:.2f}")
        print(f"  - Intent: {validation.get('intent', 'new_info')}")


async def test_correction_intent():
    """Test correction intent detection"""
    print("\n" + "=" * 60)
    print("TEST 2: Correction Intent Detection")
    print("=" * 60)

    conversation_history = [
        {"role": "user", "content": "我的房子是100平米"},
        {"role": "assistant", "content": "好的，您的房子是100平米"},
    ]

    correction_messages = [
        "不是，是120平米",
        "不对，应该是150平方米",
        "其实是200平",
    ]

    for i, message in enumerate(correction_messages, 1):
        print(f"\n📝 Test Case {i}: {message}")
        assets, profile, validation = await information_extractor.extract_information_from_conversation(
            message, conversation_history
        )

        print(f"\n✅ Intent: {validation.get('intent', 'new_info')}")
        if assets:
            print(f"   Corrected area: {assets[0].area} sqm")


async def test_fuzzy_numbers():
    """Test fuzzy number extraction"""
    print("\n" + "=" * 60)
    print("TEST 3: Fuzzy Number Extraction")
    print("=" * 60)

    test_cases = [
        "我有大概50万现金",
        "about 500k in savings",
        "房子价值差不多300万",
        "存款大约100万左右",
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {message}")
        assets, profile, validation = await information_extractor.extract_information_from_conversation(
            message
        )

        if assets:
            print(f"✅ Extracted value: {assets[0].value}")
        else:
            print("❌ No assets extracted")


async def test_profile_extraction():
    """Test user profile extraction"""
    print("\n" + "=" * 60)
    print("TEST 4: User Profile Extraction")
    print("=" * 60)

    test_cases = [
        "我今年35岁，已婚有孩子，每月支出大概2万",
        "我是90后，单身，比较保守的投资风格",
        "40多岁，家里有两个孩子，风险偏好比较激进",
    ]

    for i, message in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {message}")
        assets, profile, validation = await information_extractor.extract_information_from_conversation(
            message
        )

        if profile:
            print(f"✅ Profile extracted:")
            print(f"  - Age range: {profile.age_range}")
            print(f"  - Family: {profile.family_structure}")
            print(f"  - Monthly expense: {profile.monthly_expense}")
            print(f"  - Risk preference: {profile.risk_preference}")
        else:
            print("❌ No profile extracted")


async def test_phase2_format():
    """Test Phase 2 format extraction"""
    print("\n" + "=" * 60)
    print("TEST 5: Phase 2 Format (extract_information)")
    print("=" * 60)

    message = "我有一套北京的房子，120平米，价值500万，还有50万现金存款"
    conversation_history = []

    print(f"\n📝 Message: {message}")
    result = await extract_information(message, conversation_history)

    print(f"\n✅ Phase 2 Result:")
    print(f"  - Assets: {len(result['assets'])}")
    for asset in result["assets"]:
        print(f"    • {asset['type']}: {asset['amount']} CNY")
    print(f"  - Completeness update: {result['completeness_update']}")
    print(f"  - Intent: {result['intent']}")


async def test_mixed_assets():
    """Test extraction of multiple asset types"""
    print("\n" + "=" * 60)
    print("TEST 6: Mixed Asset Types")
    print("=" * 60)

    message = "我有一套房产价值500万，现金存款80万，股票基金大概30万，还有200万房贷"

    print(f"\n📝 Message: {message}")
    assets, profile, validation = await information_extractor.extract_information_from_conversation(
        message
    )

    print(f"\n✅ Extracted {len(assets)} asset(s):")
    for asset in assets:
        print(f"  - {asset.asset_type.value}: {asset.name} = {asset.value}")

    print(f"\n📊 Completeness: {validation['completeness_score']:.2f}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 LLM-BASED INFORMATION EXTRACTION TEST SUITE")
    print("=" * 60)

    # Check if LLM is available
    if not information_extractor.has_real_openai_key:
        print("\n⚠️  WARNING: No valid OpenAI API key found")
        print("   Tests will use fallback extraction mode")
        print("   Set OPENAI_API_KEY in backend/.env for full LLM testing")
    else:
        print("\n✅ LLM available - running full tests")

    try:
        await test_real_estate_extraction()
        await test_correction_intent()
        await test_fuzzy_numbers()
        await test_profile_extraction()
        await test_phase2_format()
        await test_mixed_assets()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
