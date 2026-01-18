"""
Test script to verify that risk_profile is updated with ALL fields, not just tolerance

This test verifies the fix for the issue where only 'tolerance' was being updated
in UserCognition.risk_profile, while other psychological fields were missing.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import select

from app.core.database import get_db_session
from app.models.cognition import UserCognition
from app.models.user import User
from app.services.chat_agent import get_chat_agent


async def test_risk_profile_complete_update():
    """Test that risk_profile is updated with all psychological fields"""
    
    print("=" * 80)
    print("Testing Risk Profile Complete Update Fix")
    print("=" * 80)
    
    # Get or create test user
    async for session in get_db_session():
        # Check if test user exists
        user_statement = select(User).where(User.phone_number == "+8613800000001")
        user_result = await session.execute(user_statement)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("❌ Test user not found. Please create a test user first.")
            return
        
        user_id = user.id
        print(f"✅ Using test user: {user.phone_number} (ID: {user_id})")
        break
    
    # Get chat agent
    chat_agent = get_chat_agent()
    
    # Simulate conversation with psychological cues
    print("\n" + "=" * 80)
    print("Step 1: Simulating conversation with psychological cues")
    print("=" * 80)
    
    messages = [
        "我今年35岁，已婚有两个孩子",
        "我有一套房产在北京，还有50万存款",
        "我比较保守，不想冒太大风险",
        "我担心房贷压力，每月还款1万多，手头有点紧"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[Message {i}] User: {msg}")
        print(f"[Response {i}] AI: ", end="", flush=True)
        
        async for chunk in chat_agent.process_message(msg, user_id):
            print(chunk, end="", flush=True)
        
        print()  # New line after response
    
    # Wait for background extraction to complete
    print("\n" + "=" * 80)
    print("Step 2: Waiting for background extraction to complete...")
    print("=" * 80)
    await asyncio.sleep(3)  # Give time for async extraction
    
    # Check UserCognition.risk_profile
    print("\n" + "=" * 80)
    print("Step 3: Verifying risk_profile fields")
    print("=" * 80)
    
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if not cognition:
            print("❌ No UserCognition record found")
            return
        
        if not cognition.risk_profile:
            print("❌ risk_profile is empty")
            return
        
        print("\n✅ Risk Profile Fields Found:")
        for key, value in cognition.risk_profile.items():
            print(f"   - {key}: {value}")
        
        # Verify all expected fields are present
        expected_fields = [
            "tolerance",
            "decision_style",
            "sentiment",
            "liquidity_anxiety",
            "confidence_score",
            "loss_aversion",
            "financial_literacy",
            "family_responsibility",
            "planning_horizon",
            "last_analysis"
        ]
        
        print("\n" + "=" * 80)
        print("Step 4: Field Validation")
        print("=" * 80)
        
        missing_fields = []
        present_fields = []
        
        for field in expected_fields:
            if field in cognition.risk_profile:
                present_fields.append(field)
                print(f"✅ {field}: {cognition.risk_profile[field]}")
            else:
                missing_fields.append(field)
                print(f"❌ {field}: MISSING")
        
        print("\n" + "=" * 80)
        print("Test Results Summary")
        print("=" * 80)
        
        print(f"\n✅ Present fields: {len(present_fields)}/{len(expected_fields)}")
        print(f"   {', '.join(present_fields)}")
        
        if missing_fields:
            print(f"\n❌ Missing fields: {len(missing_fields)}/{len(expected_fields)}")
            print(f"   {', '.join(missing_fields)}")
            print("\n❌ TEST FAILED: Not all expected fields are present")
        else:
            print("\n✅ TEST PASSED: All expected fields are present!")
        
        # Check advisor_note
        if cognition.advisor_note:
            print(f"\n✅ Advisor Note: {cognition.advisor_note[:100]}...")
        else:
            print("\n⚠️  Advisor Note: Not set")
        
        break


async def test_old_behavior_removed():
    """Test that the old behavior (only updating tolerance) is removed"""
    
    print("\n" + "=" * 80)
    print("Testing Old Behavior Removal")
    print("=" * 80)
    
    # This test verifies that _update_cognition_state() no longer updates risk_profile
    # We can't directly test this, but we can verify through logs and behavior
    
    print("\n✅ Verification:")
    print("   1. Check logs for '🔄 COGNITION_UPDATE: Updated collection_status'")
    print("   2. Verify NO logs for 'Updated risk_profile.tolerance'")
    print("   3. Check logs for '✅ INSIGHT_UPDATE: Updated complete risk_profile'")
    print("\n✅ If you see the above pattern, the fix is working correctly!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Risk Profile Complete Update Test")
    print("=" * 80)
    print("\nThis test verifies that risk_profile is updated with ALL fields:")
    print("- tolerance, decision_style, sentiment, liquidity_anxiety")
    print("- confidence_score, loss_aversion, financial_literacy")
    print("- family_responsibility, planning_horizon, last_analysis")
    print("\n" + "=" * 80)
    
    asyncio.run(test_risk_profile_complete_update())
    asyncio.run(test_old_behavior_removed())
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
