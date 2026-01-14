#!/usr/bin/env python3
"""
Test real chat scenario to debug real estate extraction issue
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.chat_agent import get_chat_agent
from app.core.database import get_db_session
from app.models.user import User, UserAsset
from app.models.cognition import UserCognition
from sqlmodel import select


async def test_real_chat_scenario():
    """Test a real chat scenario with real estate information"""
    
    print("🗣️ Testing Real Chat Scenario - Real Estate Information")
    print("=" * 60)
    
    # Create test user
    test_user_id = 99997
    
    try:
        # Setup test user
        async for session in get_db_session():
            # Clean up existing data
            existing_assets = await session.execute(
                select(UserAsset).where(UserAsset.user_id == test_user_id)
            )
            for asset in existing_assets.scalars().all():
                await session.delete(asset)
            
            existing_cognition = await session.execute(
                select(UserCognition).where(UserCognition.user_id == test_user_id)
            )
            cognition = existing_cognition.scalar_one_or_none()
            if cognition:
                await session.delete(cognition)
            
            # Create test user
            existing_user = await session.execute(
                select(User).where(User.id == test_user_id)
            )
            user = existing_user.scalar_one_or_none()
            if not user:
                test_user = User(id=test_user_id, phone="13800000002")
                session.add(test_user)
            
            await session.commit()
            break
        
        # Get chat agent
        chat_agent = get_chat_agent()
        
        # Test conversation with real estate information
        print("\n1️⃣ User says: '你好'")
        response_chunks = []
        async for chunk in chat_agent.process_message("你好", test_user_id):
            response_chunks.append(chunk)
        
        ai_response = "".join(response_chunks)
        print(f"🤖 AI Response: {ai_response[:100]}...")
        
        # Check database after first message
        await check_database_state(test_user_id, "After greeting")
        
        print("\n2️⃣ User says: '我有一套房子在北京朝阳区，大概120平米，价值600万'")
        response_chunks = []
        async for chunk in chat_agent.process_message("我有一套房子在北京朝阳区，大概120平米，价值600万", test_user_id):
            response_chunks.append(chunk)
        
        ai_response = "".join(response_chunks)
        print(f"🤖 AI Response: {ai_response[:200]}...")
        
        # Check database after real estate message
        await check_database_state(test_user_id, "After real estate info")
        
        print("\n3️⃣ User says: '我还有50万现金'")
        response_chunks = []
        async for chunk in chat_agent.process_message("我还有50万现金", test_user_id):
            response_chunks.append(chunk)
        
        ai_response = "".join(response_chunks)
        print(f"🤖 AI Response: {ai_response[:200]}...")
        
        # Check database after cash message
        await check_database_state(test_user_id, "After cash info")
        
        # Test checklist generation
        print("\n4️⃣ Testing checklist generation...")
        checklist = await chat_agent._generate_state_checklist(test_user_id)
        print("📋 Current checklist:")
        print(checklist)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await cleanup_test_user(test_user_id)


async def check_database_state(user_id: int, stage: str):
    """Check the current database state"""
    print(f"\n📊 Database State - {stage}:")
    
    async for session in get_db_session():
        # Check assets
        assets_result = await session.execute(
            select(UserAsset).where(UserAsset.user_id == user_id)
        )
        assets = assets_result.scalars().all()
        
        print(f"   🏠 Assets: {len(assets)}")
        for asset in assets:
            print(f"      - {asset.name}: {asset.value} ({asset.asset_type.value})")
            if asset.extra_data:
                location = asset.extra_data.get('location', 'N/A')
                area = asset.extra_data.get('area', 'N/A')
                print(f"        Location: {location}, Area: {area}")
        
        # Check cognition
        cognition_result = await session.execute(
            select(UserCognition).where(UserCognition.user_id == user_id)
        )
        cognition = cognition_result.scalar_one_or_none()
        
        if cognition:
            print(f"   🧠 Collection Status: {cognition.collection_status}")
            print(f"   🎯 Financial Goals: {cognition.financial_goals}")
            print(f"   ⚖️ Risk Profile: {cognition.risk_profile}")
        else:
            print(f"   ❌ No cognition record found")
        
        break


async def cleanup_test_user(user_id: int):
    """Clean up test user data"""
    try:
        async for session in get_db_session():
            # Delete assets
            existing_assets = await session.execute(
                select(UserAsset).where(UserAsset.user_id == user_id)
            )
            for asset in existing_assets.scalars().all():
                await session.delete(asset)
            
            # Delete cognition
            existing_cognition = await session.execute(
                select(UserCognition).where(UserCognition.user_id == user_id)
            )
            cognition = existing_cognition.scalar_one_or_none()
            if cognition:
                await session.delete(cognition)
            
            # Delete user
            existing_user = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = existing_user.scalar_one_or_none()
            if user:
                await session.delete(user)
            
            await session.commit()
            print("🧹 Test data cleaned up")
            break
            
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_real_chat_scenario())