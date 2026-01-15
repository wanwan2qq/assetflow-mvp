#!/usr/bin/env python3
"""
Demo script showing how the Fact Sheet prevents Context Amnesia

This script demonstrates:
1. Creating a user with specific asset details (100sqm property)
2. Showing the Fact Sheet that gets injected into AI context
3. Verifying the AI receives exact data (not 90sqm or other hallucinated values)
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import get_db_session
from app.models.user import User, UserAsset, AssetType
from app.services.chat_agent import get_chat_agent, ChatContext


async def create_demo_user():
    """Create a demo user with a 100sqm property"""
    async for session in get_db_session():
        # Create user
        user = User(phone="13900000001", device_id="demo-context-amnesia")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Add a property with EXACTLY 100sqm
        property_asset = UserAsset(
            user_id=user.id,
            asset_type=AssetType.REAL_ESTATE,
            name="北京海淀区永靓家园",
            value=4280000,  # 428万
            is_confirmed=True,
            extra_data={
                "location": "北京海淀区",
                "area": 100  # EXACTLY 100sqm - not 90, not 110
            }
        )
        session.add(property_asset)
        await session.commit()
        
        print(f"✅ Created demo user {user.id}")
        print(f"   Property: {property_asset.name}")
        print(f"   Area: {property_asset.extra_data['area']}平米 (EXACTLY 100)")
        print(f"   Value: {property_asset.value/10000:.0f}万")
        
        return user.id


async def demonstrate_fact_sheet(user_id: int):
    """Demonstrate the Fact Sheet that prevents hallucination"""
    print("\n" + "="*60)
    print("FACT SHEET DEMONSTRATION")
    print("="*60)
    
    agent = get_chat_agent()
    
    # Generate the Fact Sheet
    fact_sheet = await agent._generate_fact_sheet(user_id)
    
    print("\n📋 This is what the AI sees (Fact Sheet):")
    print("-" * 60)
    print(fact_sheet)
    print("-" * 60)
    
    # Verify the exact data
    print("\n✅ Verification:")
    checks = {
        "Contains exact area (100平米)": "100平米" in fact_sheet,
        "Contains exact value (428万)": "428万" in fact_sheet,
        "Contains location": "北京海淀区" in fact_sheet,
        "Shows confirmation status": "(用户已确认)" in fact_sheet,
        "Has anti-hallucination warning": "(请基于以上数据回答，严禁编造数据)" in fact_sheet,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    return all_passed


async def demonstrate_contextual_input(user_id: int):
    """Demonstrate the full contextual input with Fact Sheet"""
    print("\n" + "="*60)
    print("CONTEXTUAL INPUT DEMONSTRATION")
    print("="*60)
    
    agent = get_chat_agent()
    context = ChatContext(user_id=user_id)
    
    # Simulate user asking about property size
    user_message = "我的房子有多大？"
    
    # Generate contextual input (what AI actually receives)
    contextual_input = await agent._prepare_contextual_input(user_message, context, user_id)
    
    print(f"\n💬 User asks: \"{user_message}\"")
    print("\n🤖 AI receives this context:")
    print("-" * 60)
    print(contextual_input)
    print("-" * 60)
    
    # Verify AI has exact data
    print("\n✅ AI Context Verification:")
    checks = {
        "Has Fact Sheet with exact area": "100平米" in contextual_input,
        "Has user's question": user_message in contextual_input,
        "Has anti-hallucination warning": "严禁编造数据" in contextual_input,
        "Has property name": "永靓家园" in contextual_input,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    return all_passed


async def demonstrate_before_after():
    """Show the before/after comparison"""
    print("\n" + "="*60)
    print("BEFORE vs AFTER COMPARISON")
    print("="*60)
    
    print("\n❌ BEFORE (Context Amnesia):")
    print("-" * 60)
    print("AI Context: [已提取资产: 1项]")
    print("User: 我的房子有多大？")
    print("AI: 您的房子大约是90平米... (HALLUCINATION! 🚨)")
    print("     ↑ AI confused 100sqm with 90sqm")
    
    print("\n✅ AFTER (With Fact Sheet):")
    print("-" * 60)
    print("AI Context:")
    print("【当前系统已确信的资产清单 (Fact Sheet)】")
    print("1. [房产] 北京海淀区永靓家园 | 估值: 428万 | 面积: 100平米 | 位置: 北京海淀区 (用户已确认)")
    print("(请基于以上数据回答，严禁编造数据)")
    print("\nUser: 我的房子有多大？")
    print("AI: 根据记录，您在北京海淀区永靓家园的房产面积是100平米。(ACCURATE! ✅)")
    print("     ↑ AI uses exact data from Fact Sheet")


async def cleanup_demo_data():
    """Clean up demo data"""
    async for session in get_db_session():
        from sqlmodel import select
        
        users_statement = select(User).where(User.device_id == "demo-context-amnesia")
        users_result = await session.execute(users_statement)
        users = users_result.scalars().all()
        
        for user in users:
            # Delete assets
            assets_statement = select(UserAsset).where(UserAsset.user_id == user.id)
            assets_result = await session.execute(assets_statement)
            assets = assets_result.scalars().all()
            
            for asset in assets:
                await session.delete(asset)
            
            # Delete user
            await session.delete(user)
        
        await session.commit()
        print(f"\n🧹 Cleaned up {len(users)} demo users")


async def main():
    """Run the demonstration"""
    print("\n" + "="*60)
    print("CONTEXT AMNESIA FIX DEMONSTRATION")
    print("="*60)
    print("\nThis demo shows how the Fact Sheet prevents AI hallucination")
    print("by providing exact, structured asset data in the AI context.")
    
    try:
        # Create demo user
        user_id = await create_demo_user()
        
        # Demonstrate Fact Sheet
        test1_passed = await demonstrate_fact_sheet(user_id)
        
        # Demonstrate contextual input
        test2_passed = await demonstrate_contextual_input(user_id)
        
        # Show before/after comparison
        await demonstrate_before_after()
        
        # Summary
        print("\n" + "="*60)
        print("DEMONSTRATION SUMMARY")
        print("="*60)
        print(f"Fact Sheet Generation: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Contextual Input: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 Context Amnesia Fix is working correctly!")
            print("\nKey Takeaways:")
            print("  • AI receives exact data from database (100平米, not 90平米)")
            print("  • Fact Sheet shows confirmation status (用户已确认 vs 系统推测)")
            print("  • Anti-hallucination warning prevents fabrication")
            print("  • Missing information hints guide conversation")
            return 0
        else:
            print("\n❌ Some checks failed")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await cleanup_demo_data()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
