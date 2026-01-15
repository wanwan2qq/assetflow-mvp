#!/usr/bin/env python3
"""
诊断脚本：检查AI为什么无法记住用户信息
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import select
from app.core.database import get_db_session
from app.models.user import User, UserProfile, UserAsset
from app.models.cognition import UserCognition
from app.services.chat_agent import ChatAgent


async def diagnose_user_context(phone: str):
    """诊断指定用户的上下文信息"""
    
    print(f"\n{'='*80}")
    print(f"诊断用户上下文信息 - 手机号: {phone}")
    print(f"{'='*80}\n")
    
    async for session in get_db_session():
        # 1. 查找用户
        user_statement = select(User).where(User.phone == phone)
        user_result = await session.execute(user_statement)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ 未找到用户: {phone}")
            return
        
        user_id = user.id
        print(f"✓ 找到用户 ID: {user_id}\n")
        
        # 2. 检查 UserProfile (L1层)
        print("【L1层 - UserProfile】")
        profile_statement = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await session.execute(profile_statement)
        profile = profile_result.scalar_one_or_none()
        
        if profile:
            print(f"✓ UserProfile 存在")
            print(f"  - age_range: {profile.age_range}")
            print(f"  - family_structure: {profile.family_structure}")
            print(f"  - risk_preference: {profile.risk_preference}")
            print(f"  - monthly_expense: {profile.monthly_expense}")
            print(f"  - occupation: {profile.occupation}")
            print(f"  - income_range: {profile.income_range}")
        else:
            print("❌ UserProfile 不存在")
        
        # 3. 检查 UserCognition (L2层)
        print("\n【L2层 - UserCognition】")
        cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
        cognition_result = await session.execute(cognition_statement)
        cognition = cognition_result.scalar_one_or_none()
        
        if cognition:
            print(f"✓ UserCognition 存在")
            print(f"  - financial_goals: {cognition.financial_goals}")
            print(f"  - risk_profile: {cognition.risk_profile}")
            print(f"  - collection_status: {cognition.collection_status}")
            print(f"  - advisor_note: {cognition.advisor_note[:100] if cognition.advisor_note else None}...")
        else:
            print("❌ UserCognition 不存在")
        
        # 4. 检查 UserAsset
        print("\n【L1层 - UserAsset】")
        assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
        assets_result = await session.execute(assets_statement)
        assets = assets_result.scalars().all()
        
        if assets:
            print(f"✓ 找到 {len(assets)} 个资产:")
            for asset in assets:
                print(f"  - [{asset.asset_type.value}] {asset.name}: {asset.value}")
        else:
            print("❌ 没有资产记录")
        
        break
    
    # 5. 测试 Fact Sheet 生成
    print("\n" + "="*80)
    print("【AI实际看到的上下文 - Fact Sheet】")
    print("="*80 + "\n")
    
    chat_agent = ChatAgent()
    fact_sheet = await chat_agent._generate_fact_sheet(user_id)
    print(fact_sheet)
    
    # 6. 分析问题
    print("\n" + "="*80)
    print("【问题诊断】")
    print("="*80 + "\n")
    
    issues = []
    
    if not profile:
        issues.append("❌ UserProfile 不存在 - AI无法获取用户年龄、家庭、职业等信息")
    else:
        # 检查 Fact Sheet 是否包含 UserProfile 信息
        if profile.age_range and profile.age_range not in fact_sheet:
            issues.append(f"⚠️  UserProfile.age_range ({profile.age_range}) 未出现在 Fact Sheet 中")
        if profile.family_structure and profile.family_structure not in fact_sheet:
            issues.append(f"⚠️  UserProfile.family_structure ({profile.family_structure}) 未出现在 Fact Sheet 中")
        if profile.occupation and profile.occupation not in fact_sheet:
            issues.append(f"⚠️  UserProfile.occupation ({profile.occupation}) 未出现在 Fact Sheet 中")
        if profile.income_range and profile.income_range not in fact_sheet:
            issues.append(f"⚠️  UserProfile.income_range ({profile.income_range}) 未出现在 Fact Sheet 中")
    
    if not cognition:
        issues.append("❌ UserCognition 不存在 - AI无法获取用户风险偏好和收集状态")
    
    if issues:
        print("发现以下问题:\n")
        for issue in issues:
            print(issue)
        
        print("\n【根本原因】")
        print("_generate_fact_sheet() 方法只读取了 UserCognition.risk_profile['tolerance']")
        print("但没有读取 UserProfile 表中的完整用户画像信息！")
        
        print("\n【建议修复】")
        print("在 _generate_fact_sheet() 中添加 UserProfile 信息的读取和展示")
    else:
        print("✓ 未发现明显问题")


async def main():
    """主函数"""
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        # 默认使用测试用户
        phone = input("请输入用户手机号（或按回车使用默认测试用户）: ").strip()
        if not phone:
            phone = "13800000000"  # 默认测试用户
    
    await diagnose_user_context(phone)


if __name__ == "__main__":
    asyncio.run(main())
