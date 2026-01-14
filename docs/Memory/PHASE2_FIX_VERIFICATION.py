#!/usr/bin/env python3
"""
Phase 2 Fix Verification - Final Test
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


async def verify_phase2_fix():
    """Verify Phase 2 fix works correctly"""
    
    print("🎯 Phase 2 Fix Verification")
    print("=" * 50)
    
    test_user_id = 99999
    
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
                test_user = User(id=test_user_id, phone="13999999999")
                session.add(test_user)
            
            await session.commit()
            break
        
        # Get chat agent
        chat_agent = get_chat_agent()
        
        print("\n1️⃣ User mentions real estate")
        response_chunks = []
        async for chunk in chat_agent.process_message("我有一套房子在北京朝阳区，120平米", test_user_id):
            response_chunks.append(chunk)
        
        await check_state(test_user_id, "After real estate")
        
        print("\n2️⃣ User mentions cash")
        response_chunks = []
        async for chunk in chat_agent.process_message("我还有50万现金", test_user_id):
            response_chunks.append(chunk)
        
        await check_state(test_user_id, "After cash")
        
        # Generate checklist
        print("\n3️⃣ Checking final checklist")
        checklist = await chat_agent._generate_state_checklist(test_user_id)
        print("📋 Final checklist:")
        print(checklist)
        
        # Verify expectations
        if "[✅] 房产" in checklist and "[✅] 现金" in checklist:
            print("\n🎉 SUCCESS: Both real estate and cash are marked as collected!")
            return True
        else:
            print("\n❌ FAILED: Checklist doesn't show both assets as collected")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        await cleanup_test_user(test_user_id)


async def check_state(user_id: int, stage: str):
    """Check current state"""
    print(f"\n📊 {stage}:")
    
    async for session in get_db_session():
        # Check assets
        assets_result = await session.execute(
            select(UserAsset).where(UserAsset.user_id == user_id)
        )
        assets = assets_result.scalars().all()
        
        print(f"   Assets: {len(assets)}")
        for asset in assets:
            print(f"     - {asset.name}: {asset.value} ({asset.asset_type.value})")
        
        # Check cognition
        cognition_result = await session.execute(
            select(UserCognition).where(UserCognition.user_id == user_id)
        )
        cognition = cognition_result.scalar_one_or_none()
        
        if cognition:
            print(f"   Collection Status: {cognition.collection_status}")
        else:
            print(f"   No cognition record")
        
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
            print("🧹 Cleaned up")
            break
            
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")


if __name__ == "__main__":
    async def main():
        success = await verify_phase2_fix()
        if success:
            print("\n✅ Phase 2 房产信息提取和状态同步 - 修复成功！")
        else:
            print("\n❌ Phase 2 仍有问题需要进一步调试")
            sys.exit(1)
    
    asyncio.run(main())