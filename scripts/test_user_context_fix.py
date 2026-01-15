#!/usr/bin/env python3
"""
测试用户上下文修复：验证AI能否正确读取和使用用户画像信息
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import select
from app.core.database import get_db_session
from app.models.user import User, UserProfile
from app.models.cognition import UserCognition
from app.services.asset_extraction_service import asset_extraction_service
from app.services.chat_agent import ChatAgent


async def test_user_context_fix():
    """测试用户上下文修复"""
    
    print("\n" + "="*80)
    print("测试用户上下文修复 - AI能否记住用户信息")
    print("="*80 + "\n")
    
    # 1. 创建测试用户
    async for session in get_db_session():
        test_phone = "13900000099"
        existing_user = (await session.execute(
            select(User).where(User.phone == test_phone)
        )).scalar_one_or_none()
        
        if existing_user:
            await session.delete(existing_user)
            await session.commit()
        
        test_user = User(phone=test_phone)
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id
        print(f"✓ 创建测试用户 ID: {user_id}\n")
        break
    
    # 2. 模拟用户提供个人信息
    print("【步骤1】用户提供个人信息")
    print("用户说: '我今年35岁，已婚有一个孩子，是软件工程师，年收入大概30-50万'")
    
    extraction_result = {
        "assets": [],
        "goals": [],
        "risk_profile": {
            "age_range": "30-40",
            "family_structure": "married_with_kids",
            "occupation": "软件工程师",
            "income_range": "30-50万",
            "tolerance": "moderate"
        },
        "completeness_update": {}
    }
    
    success = await asset_extraction_service.update_user_state(user_id, extraction_result)
    print(f"信息提取结果: {'成功' if success else '失败'}\n")
    
    # 3. 验证数据已保存
    print("【步骤2】验证数据已保存到数据库")
    async for session in get_db_session():
        profile = (await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )).scalar_one_or_none()
        
        cognition = (await session.execute(
            select(UserCognition).where(UserCognition.user_id == user_id)
        )).scalar_one_or_none()
        
        if profile:
            print("✓ UserProfile 已创建:")
            print(f"  - age_range: {profile.age_range}")
            print(f"  - family_structure: {profile.family_structure}")
            print(f"  - occupation: {profile.occupation}")
            print(f"  - income_range: {profile.income_range}")
            print(f"  - risk_preference: {profile.risk_preference}")
        else:
            print("❌ UserProfile 未创建")
            return False
        
        if cognition:
            print("\n✓ UserCognition 已创建:")
            print(f"  - risk_profile: {cognition.risk_profile}")
        else:
            print("\n❌ UserCognition 未创建")
        
        break
    
    # 4. 测试 Fact Sheet 生成（修复前后对比）
    print("\n" + "="*80)
    print("【步骤3】测试 Fact Sheet 生成（AI实际看到的上下文）")
    print("="*80 + "\n")
    
    chat_agent = ChatAgent()
    fact_sheet = await chat_agent._generate_fact_sheet(user_id)
    
    print("生成的 Fact Sheet:")
    print("-" * 80)
    print(fact_sheet)
    print("-" * 80)
    
    # 5. 验证修复效果
    print("\n" + "="*80)
    print("【步骤4】验证修复效果")
    print("="*80 + "\n")
    
    checks = []
    
    # 检查年龄是否出现
    if "30-40" in fact_sheet or "35" in fact_sheet:
        print("✓ 年龄信息已包含在 Fact Sheet 中")
        checks.append(True)
    else:
        print("❌ 年龄信息未包含在 Fact Sheet 中")
        checks.append(False)
    
    # 检查家庭结构
    if "已婚有子女" in fact_sheet or "married_with_kids" in fact_sheet:
        print("✓ 家庭结构已包含在 Fact Sheet 中")
        checks.append(True)
    else:
        print("❌ 家庭结构未包含在 Fact Sheet 中")
        checks.append(False)
    
    # 检查职业
    if "软件工程师" in fact_sheet:
        print("✓ 职业信息已包含在 Fact Sheet 中")
        checks.append(True)
    else:
        print("❌ 职业信息未包含在 Fact Sheet 中")
        checks.append(False)
    
    # 检查收入
    if "30-50万" in fact_sheet:
        print("✓ 收入信息已包含在 Fact Sheet 中")
        checks.append(True)
    else:
        print("❌ 收入信息未包含在 Fact Sheet 中")
        checks.append(False)
    
    # 检查风险偏好
    if "稳健型" in fact_sheet or "moderate" in fact_sheet:
        print("✓ 风险偏好已包含在 Fact Sheet 中")
        checks.append(True)
    else:
        print("❌ 风险偏好未包含在 Fact Sheet 中")
        checks.append(False)
    
    # 总结
    print("\n" + "="*80)
    print("【测试结果】")
    print("="*80 + "\n")
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 测试通过！({passed}/{total})")
        print("\n✓ AI现在可以正确读取和使用用户画像信息了！")
        print("✓ 用户提供的年龄、家庭、职业、收入等信息都会被AI记住")
        return True
    else:
        print(f"❌ 测试失败 ({passed}/{total})")
        print("\n部分用户信息仍未被正确注入到AI上下文中")
        return False


async def main():
    """主函数"""
    try:
        result = await test_user_context_fix()
        return 0 if result else 1
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
