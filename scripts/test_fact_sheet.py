#!/usr/bin/env python3
"""
Test script for Fact Sheet generation in ChatAgent
Verifies that the AI receives structured asset data to prevent hallucination
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import get_db_session
from app.models.user import User, UserAsset, AssetType
from app.services.chat_agent import get_chat_agent


async def setup_test_user():
    """Create a test user with sample assets"""
    async for session in get_db_session():
        # Check if test user already exists
        from sqlmodel import select
        existing_statement = select(User).where(User.device_id == "test-device-fact-sheet")
        existing_result = await session.execute(existing_statement)
        user = existing_result.scalar_one_or_none()
        
        if user:
            # Clean up existing assets
            assets_statement = select(UserAsset).where(UserAsset.user_id == user.id)
            assets_result = await session.execute(assets_statement)
            assets = assets_result.scalars().all()
            for asset in assets:
                await session.delete(asset)
            await session.commit()
        else:
            # Create test user
            user = User(phone="13800000001", device_id="test-device-fact-sheet")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Add sample assets
        assets = [
            UserAsset(
                user_id=user.id,
                asset_type=AssetType.REAL_ESTATE,
                name="北京海淀区永靓家园",
                value=4280000,  # 428万
                is_confirmed=True,
                extra_data={
                    "location": "北京海淀区",
                    "area": 100
                }
            ),
            UserAsset(
                user_id=user.id,
                asset_type=AssetType.CASH,
                name="现金储蓄",
                value=100000,  # 10万
                is_confirmed=True,
                extra_data={}
            ),
            UserAsset(
                user_id=user.id,
                asset_type=AssetType.INVESTMENT,
                name="股票基金",
                value=500000,  # 50万
                is_confirmed=False,  # Not confirmed
                extra_data={}
            )
        ]
        
        for asset in assets:
            session.add(asset)
        
        await session.commit()
        
        print(f"✅ Created test user {user.id} with {len(assets)} assets")
        return user.id


async def test_fact_sheet_generation():
    """Test the Fact Sheet generation"""
    print("\n" + "="*60)
    print("Testing Fact Sheet Generation")
    print("="*60 + "\n")
    
    # Setup test user
    user_id = await setup_test_user()
    
    # Get chat agent
    agent = get_chat_agent()
    
    # Generate fact sheet
    fact_sheet = await agent._generate_fact_sheet(user_id)
    
    print("Generated Fact Sheet:")
    print("-" * 60)
    print(fact_sheet)
    print("-" * 60)
    
    # Verify fact sheet content
    checks = {
        "Has header": "【当前系统已确信的资产清单 (Fact Sheet)】" in fact_sheet,
        "Shows real estate": "北京海淀区永靓家园" in fact_sheet,
        "Shows value": "428万" in fact_sheet,
        "Shows area": "100平米" in fact_sheet,
        "Shows confirmation": "(用户已确认)" in fact_sheet,
        "Shows cash": "[现金]" in fact_sheet,
        "Shows investment": "[投资]" in fact_sheet,
        "Shows unconfirmed": "(系统推测)" in fact_sheet,
        "Has missing info": "【缺失信息提示】" in fact_sheet,
        "Has warning": "(请基于以上数据回答，严禁编造数据)" in fact_sheet
    }
    
    print("\n✅ Verification Results:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


async def test_contextual_input():
    """Test the full contextual input preparation"""
    print("\n" + "="*60)
    print("Testing Contextual Input Preparation")
    print("="*60 + "\n")
    
    # Setup test user
    user_id = await setup_test_user()
    
    # Get chat agent
    agent = get_chat_agent()
    
    # Create a mock context
    from app.services.chat_agent import ChatContext
    context = ChatContext(user_id=user_id)
    
    # Prepare contextual input
    message = "我的房子现在值多少钱？"
    contextual_input = await agent._prepare_contextual_input(message, context, user_id)
    
    print("Generated Contextual Input:")
    print("-" * 60)
    print(contextual_input)
    print("-" * 60)
    
    # Verify contextual input
    checks = {
        "Has Fact Sheet": "【当前系统已确信的资产清单 (Fact Sheet)】" in contextual_input,
        "Has user message": "我的房子现在值多少钱？" in contextual_input,
        "Has asset details": "北京海淀区永靓家园" in contextual_input,
        "Has stage hint": "[系统提示:" in contextual_input
    }
    
    print("\n✅ Verification Results:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    return all_passed


async def cleanup_test_data():
    """Clean up test data"""
    async for session in get_db_session():
        from sqlmodel import select
        
        # Delete test users
        users_statement = select(User).where(User.device_id == "test-device-fact-sheet")
        users_result = await session.execute(users_statement)
        users = users_result.scalars().all()
        
        for user in users:
            # Delete assets first
            assets_statement = select(UserAsset).where(UserAsset.user_id == user.id)
            assets_result = await session.execute(assets_statement)
            assets = assets_result.scalars().all()
            
            for asset in assets:
                await session.delete(asset)
            
            # Delete user
            await session.delete(user)
        
        await session.commit()
        print(f"\n🧹 Cleaned up {len(users)} test users")


async def main():
    """Run all tests"""
    try:
        # Test 1: Fact Sheet generation
        test1_passed = await test_fact_sheet_generation()
        
        # Test 2: Contextual input preparation
        test2_passed = await test_contextual_input()
        
        # Summary
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        print(f"Fact Sheet Generation: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Contextual Input: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        await cleanup_test_data()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
