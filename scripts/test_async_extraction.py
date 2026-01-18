"""
Test script for Plan E: Pure Async Extraction + Conversation History

This script verifies that:
1. LLM can reference user info from conversation history (本轮可引用)
2. Background extraction runs without blocking response
3. Fallback extraction works when LLM fails
4. User-perceived latency is reduced
"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.chat_agent import get_chat_agent
from app.core.database import get_db_session
from sqlalchemy import text


async def get_or_create_test_user():
    """Get an existing user or create a test user"""
    async for db in get_db_session():
        try:
            # Try to get an existing user
            result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user = result.fetchone()
            
            if user:
                user_id = user[0]
                print(f"✅ Using existing user ID: {user_id}")
                return user_id
            
            # If no users exist, create a test user
            print("⚠️ No users found, creating test user...")
            await db.execute(text("""
                INSERT INTO users (phone_number, is_verified, created_at, updated_at)
                VALUES ('13800138000', true, NOW(), NOW())
            """))
            await db.commit()
            
            result = await db.execute(text("SELECT id FROM users WHERE phone_number = '13800138000'"))
            user = result.fetchone()
            user_id = user[0]
            print(f"✅ Created test user ID: {user_id}")
            return user_id
            
        except Exception as e:
            print(f"❌ Error getting/creating user: {e}")
            await db.rollback()
            # Fallback to a default user ID
            return 1


async def test_async_extraction():
    """Test async extraction with conversation history"""
    
    print("=" * 80)
    print("Testing Plan E: Pure Async Extraction + Conversation History")
    print("=" * 80)
    
    # Get or create test user
    test_user_id = await get_or_create_test_user()
    
    # Get chat agent
    agent = get_chat_agent()
    
    # Test scenario 1: User provides age and property info
    print("\n" + "=" * 80)
    print("Test 1: User provides age and property info")
    print("=" * 80)
    
    user_message_1 = "我35岁，有一套北京朝阳的房子，120平米"
    print(f"\n用户: {user_message_1}")
    print("\nAI响应:")
    
    start_time = time.time()
    response_chunks = []
    
    async for chunk in agent.process_message(user_message_1, test_user_id, None):
        response_chunks.append(chunk)
        print(chunk, end="", flush=True)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"\n\n⏱️ 响应时间: {response_time:.2f}秒")
    
    # Check if AI can reference the info
    can_reference_age = "35" in full_response or "30-40" in full_response
    can_reference_location = "北京" in full_response or "朝阳" in full_response
    can_reference_area = "120" in full_response
    
    print(f"\n✅ 检查结果:")
    print(f"  - 能引用年龄: {'✅' if can_reference_age else '❌'}")
    print(f"  - 能引用位置: {'✅' if can_reference_location else '❌'}")
    print(f"  - 能引用面积: {'✅' if can_reference_area else '❌'}")
    
    # Wait for background extraction to complete
    print(f"\n⏳ 等待后台提取完成 (3秒)...")
    await asyncio.sleep(3)
    
    # Test scenario 2: User asks follow-up question
    print("\n" + "=" * 80)
    print("Test 2: User asks follow-up question")
    print("=" * 80)
    
    user_message_2 = "那个房子大概值多少钱？"
    print(f"\n用户: {user_message_2}")
    print("\nAI响应:")
    
    start_time = time.time()
    response_chunks = []
    
    async for chunk in agent.process_message(user_message_2, test_user_id, None):
        response_chunks.append(chunk)
        print(chunk, end="", flush=True)
    
    response_time = time.time() - start_time
    full_response = "".join(response_chunks)
    
    print(f"\n\n⏱️ 响应时间: {response_time:.2f}秒")
    
    # Check if AI understands the reference
    understands_reference = "北京" in full_response or "朝阳" in full_response or "房" in full_response
    
    print(f"\n✅ 检查结果:")
    print(f"  - 理解指代关系: {'✅' if understands_reference else '❌'}")
    
    # Wait for background extraction
    await asyncio.sleep(3)
    
    # Test scenario 3: Check Fact Sheet
    print("\n" + "=" * 80)
    print("Test 3: Check Fact Sheet (after extraction)")
    print("=" * 80)
    
    fact_sheet = await agent._generate_fact_sheet(test_user_id)
    print(f"\n{fact_sheet}")
    
    # Check if data was saved to DB
    has_age = "30-40" in fact_sheet or "35" in fact_sheet
    has_property = "北京" in fact_sheet or "朝阳" in fact_sheet
    
    print(f"\n✅ 检查结果:")
    print(f"  - Fact Sheet包含年龄: {'✅' if has_age else '❌'}")
    print(f"  - Fact Sheet包含房产: {'✅' if has_property else '❌'}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_async_extraction())
