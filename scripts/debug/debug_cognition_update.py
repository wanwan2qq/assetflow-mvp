#!/usr/bin/env python3
"""
Debug script to test cognition update directly
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.asset_extraction_service import asset_extraction_service
from app.core.database import get_db_session
from app.models.user import User, UserAsset
from app.models.cognition import UserCognition
from sqlmodel import select


async def test_cognition_update():
    """Test cognition update directly"""
    
    print("🔍 Testing Cognition Update")
    print("=" * 50)
    
    test_user_id = 77777
    
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
                test_user = User(id=test_user_id, phone=f"1377777{test_user_id}")
                session.add(test_user)
            
            await session.commit()
            break
        
        # Test 1: Real estate extraction
        print("\n1️⃣ Testing real estate extraction")
        extraction_result1 = {
            "assets": [
                {
                    "type": "real_estate",
                    "amount": 5130000,
                    "currency": "CNY",
                    "name": "房产",
                    "location": "北京朝阳区",
                    "area": 120.0
                }
            ],
            "goals": [],
            "risk_profile": {},
            "completeness_update": {
                "real_estate": True
            }
        }
        
        success1 = await asset_extraction_service.update_user_state(test_user_id, extraction_result1)
        print(f"Real estate update success: {success1}")
        
        # Check state after real estate
        await check_state(test_user_id, "After real estate")
        
        # Test 2: Cash extraction
        print("\n2️⃣ Testing cash extraction")
        extraction_result2 = {
            "assets": [
                {
                    "type": "cash",
                    "amount": 500000,
                    "currency": "CNY",
                    "name": "现金"
                }
            ],
            "goals": [],
            "risk_profile": {},
            "completeness_update": {
                "cash": True
            }
        }
        
        success2 = await asset_extraction_service.update_user_state(test_user_id, extraction_result2)
        print(f"Cash update success: {success2}")
        
        # Check final state
        await check_state(test_user_id, "After cash")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
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
    asyncio.run(test_cognition_update())