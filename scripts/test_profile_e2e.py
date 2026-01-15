#!/usr/bin/env python3
"""
End-to-end test for profile extraction in chat flow
Tests that occupation and income_range flow through the entire system
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.chat_agent import ChatAgent
from app.core.database import get_db_session
from app.models.cognition import UserCognition
from app.models.user import User
from sqlmodel import select


async def test_profile_e2e():
    """Test profile extraction through chat agent"""
    
    print("=" * 80)
    print("End-to-End Profile Extraction Test")
    print("=" * 80)
    
    # Get or create test user
    async for session in get_db_session():
        # Find existing user or use user 1
        statement = select(User).limit(1)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ No users found in database. Please create a user first.")
            return
        
        user_id = user.id
        print(f"\n📱 Using test user: {user_id} (phone: {user.phone})")
        break
    
    # Initialize chat agent
    chat_agent = ChatAgent()
    
    # Test messages with profile information
    test_messages = [
        "你好，我想了解一下理财建议",
        "我是一名软件工程师，月收入大概8万元",
        "我今年35岁，已婚有一个孩子",
        "我比较保守，不喜欢高风险投资"
    ]
    
    print("\n" + "=" * 80)
    print("Simulating Chat Conversation")
    print("=" * 80)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n💬 Message {i}: {message}")
        
        try:
            response = await chat_agent.process_message(user_id, message)
            print(f"🤖 Response: {response[:100]}..." if len(response) > 100 else f"🤖 Response: {response}")
        except Exception as e:
            print(f"⚠️  Error processing message: {e}")
    
    # Verify stored data
    print("\n" + "=" * 80)
    print("Verifying Stored Profile Data")
    print("=" * 80)
    
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if cognition and cognition.risk_profile:
            print(f"\n✅ UserCognition.risk_profile found:")
            print(f"   Full data: {cognition.risk_profile}")
            
            # Check specific fields
            checks = {
                "occupation": "职业信息",
                "income_range": "收入范围",
                "age_range": "年龄段",
                "family_structure": "家庭结构",
                "tolerance": "风险偏好"
            }
            
            print(f"\n📊 Field Verification:")
            all_present = True
            for field, description in checks.items():
                value = cognition.risk_profile.get(field)
                status = "✅" if value else "❌"
                print(f"   {status} {description} ({field}): {value}")
                if not value:
                    all_present = False
            
            # Final verdict
            print("\n" + "=" * 80)
            if all_present:
                print("✅ SUCCESS: All profile fields are properly extracted and stored!")
            else:
                print("⚠️  PARTIAL: Some profile fields are missing")
                print("   This may be due to LLM extraction or conversation flow")
            print("=" * 80)
            
        else:
            print(f"\n❌ No UserCognition record found for user {user_id}")
            print("   The chat agent may not have triggered profile extraction")
        
        break
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_profile_e2e())
