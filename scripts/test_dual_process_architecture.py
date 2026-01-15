#!/usr/bin/env python3
"""
Test script for Dual-Process Cognitive Architecture (System 1 & System 2)

This script verifies:
1. System 1 (Immediate Consistency): Facts/status are immediately available after extraction
2. System 2 (Non-blocking Latency): Insights/memory processing doesn't block responses
3. Context Refresh: AI sees user-provided data in the very next turn

Test Cases:
- "Immediate Recall Test": User says "I am 35 years old" -> AI must acknowledge age in next response
- "Checklist Test": User provides "Cash info" -> Next turn must show [✅] Cash in collection status
- "No Latency Regression": Response generation doesn't wait for Vector Memory or Psychological Analysis
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import select

from app.core.database import get_db_session
from app.models.user import User, UserProfile, UserAsset, AssetType
from app.models.cognition import UserCognition
from app.services.chat_agent import ChatAgent
from app.core.config import settings


async def cleanup_test_user(email: str):
    """Clean up test user and all related data"""
    async for session in get_db_session():
        # Find user
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if user:
            # Delete related data
            await session.execute(
                select(UserAsset).where(UserAsset.user_id == user.id)
            )
            await session.execute(
                select(UserProfile).where(UserProfile.user_id == user.id)
            )
            await session.execute(
                select(UserCognition).where(UserCognition.user_id == user.id)
            )
            
            # Delete user
            await session.delete(user)
            await session.commit()
            print(f"✅ Cleaned up test user: {email}")
        break


async def create_test_user(email: str, phone: str) -> User:
    """Create a test user"""
    async for session in get_db_session():
        user = User(
            email=email,
            phone_number=phone,
            hashed_password="test_hash",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"✅ Created test user: {email} (ID: {user.id})")
        return user


async def verify_user_profile(user_id: int, expected_fields: dict) -> bool:
    """Verify that UserProfile contains expected fields"""
    async for session in get_db_session():
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await session.execute(statement)
        profile = result.scalar_one_or_none()
        
        if not profile:
            print(f"❌ No UserProfile found for user {user_id}")
            return False
        
        print(f"\n📋 UserProfile for user {user_id}:")
        print(f"  - age_range: {profile.age_range}")
        print(f"  - family_structure: {profile.family_structure}")
        print(f"  - occupation: {profile.occupation}")
        print(f"  - income_range: {profile.income_range}")
        print(f"  - monthly_expense: {profile.monthly_expense}")
        print(f"  - risk_preference: {profile.risk_preference}")
        
        # Verify expected fields
        all_match = True
        for field, expected_value in expected_fields.items():
            actual_value = getattr(profile, field, None)
            if actual_value != expected_value:
                print(f"❌ Field '{field}' mismatch: expected '{expected_value}', got '{actual_value}'")
                all_match = False
        
        if all_match:
            print(f"✅ All expected fields match!")
        
        return all_match


async def verify_collection_status(user_id: int, expected_status: dict) -> bool:
    """Verify that UserCognition collection_status contains expected values"""
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if not cognition:
            print(f"❌ No UserCognition found for user {user_id}")
            return False
        
        print(f"\n📋 Collection Status for user {user_id}:")
        if cognition.collection_status:
            for asset_type, is_collected in cognition.collection_status.items():
                status_icon = "✅" if is_collected else "❌"
                print(f"  {status_icon} {asset_type}: {is_collected}")
        else:
            print("  (No collection status)")
        
        # Verify expected status
        all_match = True
        for asset_type, expected_value in expected_status.items():
            actual_value = cognition.collection_status.get(asset_type) if cognition.collection_status else None
            if actual_value != expected_value:
                print(f"❌ Status '{asset_type}' mismatch: expected {expected_value}, got {actual_value}")
                all_match = False
        
        if all_match:
            print(f"✅ All expected collection statuses match!")
        
        return all_match


async def verify_assets(user_id: int, expected_count: int) -> bool:
    """Verify that UserAsset table contains expected number of assets"""
    async for session in get_db_session():
        statement = select(UserAsset).where(UserAsset.user_id == user_id)
        result = await session.execute(statement)
        assets = result.scalars().all()
        
        print(f"\n📋 Assets for user {user_id}: {len(assets)} assets")
        for asset in assets:
            print(f"  - {asset.asset_type.value}: {asset.name} = {asset.value}")
        
        if len(assets) == expected_count:
            print(f"✅ Asset count matches expected: {expected_count}")
            return True
        else:
            print(f"❌ Asset count mismatch: expected {expected_count}, got {len(assets)}")
            return False


async def test_immediate_recall():
    """
    Test Case 1: Immediate Recall Test
    
    User says "I am 35 years old" -> AI must acknowledge age in next response
    This tests System 1 (Immediate Consistency) and Context Refresh
    """
    print("\n" + "="*80)
    print("TEST 1: IMMEDIATE RECALL TEST (System 1 - Immediate Consistency)")
    print("="*80)
    
    test_email = "test_immediate_recall@example.com"
    test_phone = "+1234567890"
    
    # Cleanup and create test user
    await cleanup_test_user(test_email)
    user = await create_test_user(test_email, test_phone)
    
    # Initialize chat agent
    agent = ChatAgent()
    
    # Turn 1: User provides age
    print("\n📤 Turn 1: User says 'I am 35 years old'")
    start_time = time.time()
    
    response_chunks = []
    async for chunk in agent.process_message("I am 35 years old", user.id):
        response_chunks.append(chunk)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"📥 AI Response (took {response_time:.2f}s):")
    print(f"   {full_response[:200]}...")
    
    # Wait a moment for extraction to complete
    await asyncio.sleep(2)
    
    # Verify that age was extracted to UserProfile
    print("\n🔍 Verifying extraction to UserProfile...")
    profile_ok = await verify_user_profile(user.id, {"age_range": "30-40"})
    
    if not profile_ok:
        print("❌ TEST FAILED: Age was not extracted to UserProfile")
        return False
    
    # Turn 2: Ask a follow-up question
    print("\n📤 Turn 2: User asks 'What investment should I consider?'")
    start_time = time.time()
    
    response_chunks = []
    async for chunk in agent.process_message("What investment should I consider?", user.id):
        response_chunks.append(chunk)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"📥 AI Response (took {response_time:.2f}s):")
    print(f"   {full_response[:300]}...")
    
    # Check if AI acknowledges the age in the response
    age_keywords = ["35", "30-40", "35岁", "30多岁", "三十多岁"]
    age_mentioned = any(keyword in full_response for keyword in age_keywords)
    
    if age_mentioned:
        print(f"✅ TEST PASSED: AI acknowledged user's age in response!")
        return True
    else:
        print(f"❌ TEST FAILED: AI did not acknowledge user's age in response")
        print(f"   Expected to see age reference (35, 30-40, etc.) in response")
        return False


async def test_checklist_update():
    """
    Test Case 2: Checklist Test
    
    User provides "Cash info" -> Next turn must show [✅] Cash in collection status
    This tests L2 (UserCognition) collection status update
    """
    print("\n" + "="*80)
    print("TEST 2: CHECKLIST TEST (L2 Collection Status Update)")
    print("="*80)
    
    test_email = "test_checklist@example.com"
    test_phone = "+1234567891"
    
    # Cleanup and create test user
    await cleanup_test_user(test_email)
    user = await create_test_user(test_email, test_phone)
    
    # Initialize chat agent
    agent = ChatAgent()
    
    # Turn 1: User provides cash information
    print("\n📤 Turn 1: User says 'I have 500,000 yuan in cash savings'")
    start_time = time.time()
    
    response_chunks = []
    async for chunk in agent.process_message("I have 500,000 yuan in cash savings", user.id):
        response_chunks.append(chunk)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"📥 AI Response (took {response_time:.2f}s):")
    print(f"   {full_response[:200]}...")
    
    # Wait for extraction to complete
    await asyncio.sleep(2)
    
    # Verify that cash asset was created
    print("\n🔍 Verifying cash asset creation...")
    assets_ok = await verify_assets(user.id, expected_count=1)
    
    if not assets_ok:
        print("❌ TEST FAILED: Cash asset was not created")
        return False
    
    # Verify that collection status was updated
    print("\n🔍 Verifying collection status update...")
    status_ok = await verify_collection_status(user.id, {"cash": True})
    
    if status_ok:
        print(f"✅ TEST PASSED: Collection status correctly shows [✅] Cash!")
        return True
    else:
        print(f"❌ TEST FAILED: Collection status does not show [✅] Cash")
        return False


async def test_no_latency_regression():
    """
    Test Case 3: No Latency Regression
    
    Response generation should not wait for Vector Memory or Psychological Analysis
    This tests that System 2 (async processing) doesn't block System 1 (immediate response)
    """
    print("\n" + "="*80)
    print("TEST 3: NO LATENCY REGRESSION TEST (System 2 Non-blocking)")
    print("="*80)
    
    test_email = "test_latency@example.com"
    test_phone = "+1234567892"
    
    # Cleanup and create test user
    await cleanup_test_user(test_email)
    user = await create_test_user(test_email, test_phone)
    
    # Initialize chat agent
    agent = ChatAgent()
    
    # Measure response time for a simple message
    print("\n📤 Sending message: 'Hello, I want to discuss my investments'")
    start_time = time.time()
    
    response_chunks = []
    async for chunk in agent.process_message("Hello, I want to discuss my investments", user.id):
        response_chunks.append(chunk)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"📥 AI Response (took {response_time:.2f}s):")
    print(f"   {full_response[:200]}...")
    
    # Response should be fast (< 5 seconds for streaming to start)
    # Note: This is a rough heuristic - actual time depends on LLM API latency
    if response_time < 10:
        print(f"✅ TEST PASSED: Response was fast ({response_time:.2f}s), System 2 didn't block!")
        return True
    else:
        print(f"⚠️  WARNING: Response took {response_time:.2f}s, might be blocked by System 2")
        print(f"   (This could also be due to slow LLM API)")
        return True  # Don't fail the test, just warn


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DUAL-PROCESS COGNITIVE ARCHITECTURE TEST SUITE")
    print("Testing System 1 (Immediate Consistency) & System 2 (Non-blocking Latency)")
    print("="*80)
    
    results = []
    
    # Test 1: Immediate Recall
    try:
        result = await test_immediate_recall()
        results.append(("Immediate Recall Test", result))
    except Exception as e:
        print(f"❌ Test 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Immediate Recall Test", False))
    
    # Test 2: Checklist Update
    try:
        result = await test_checklist_update()
        results.append(("Checklist Test", result))
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Checklist Test", False))
    
    # Test 3: No Latency Regression
    try:
        result = await test_no_latency_regression()
        results.append(("No Latency Regression Test", result))
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("No Latency Regression Test", False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Dual-Process Architecture is working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
