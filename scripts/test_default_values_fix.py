"""
测试默认值修复

验证当用户没有提供年龄和家庭结构时，系统不会自动添加默认值
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.information_extraction import InformationExtractor
from app.services.asset_extraction_service import asset_extraction_service
from app.core.database import get_db_session
from sqlalchemy import text


async def test_no_default_values():
    """测试：没有提供年龄和家庭结构时，不应该创建profile"""
    
    print("=" * 80)
    print("测试：默认值修复验证")
    print("=" * 80)
    
    # 获取或创建测试用户
    async for db in get_db_session():
        try:
            # 清理测试用户的profile
            result = await db.execute(text("SELECT id FROM users LIMIT 1"))
            user = result.fetchone()
            
            if not user:
                print("❌ 没有找到测试用户")
                return
            
            user_id = user[0]
            print(f"\n使用测试用户 ID: {user_id}")
            
            # 删除现有的profile（如果存在）
            await db.execute(text(f"DELETE FROM userprofile WHERE user_id = {user_id}"))
            await db.commit()
            print(f"✅ 清理了用户 {user_id} 的现有profile")
            
            break
        except Exception as e:
            print(f"❌ 数据库操作失败: {e}")
            await db.rollback()
            return
    
    # 测试场景1: 只提供职业，没有年龄和家庭结构
    print("\n" + "=" * 80)
    print("场景1: 只提供职业，没有年龄和家庭结构")
    print("=" * 80)
    
    message_1 = "我是一名软件工程师"
    print(f"\n用户消息: {message_1}")
    
    extractor = InformationExtractor()
    result = await extractor.extract_information(message_1)
    
    print(f"\n提取结果:")
    print(f"  - 职业: {result.get('risk_profile', {}).get('occupation')}")
    print(f"  - 年龄段: {result.get('risk_profile', {}).get('age_range')}")
    print(f"  - 家庭结构: {result.get('risk_profile', {}).get('family_structure')}")
    
    # 尝试更新用户状态
    success = await asset_extraction_service.update_user_state(user_id, result)
    print(f"\n更新用户状态: {'成功' if success else '失败'}")
    
    # 检查数据库中是否创建了profile
    async for db in get_db_session():
        try:
            result = await db.execute(
                text(f"SELECT age_range, family_structure, occupation FROM userprofile WHERE user_id = {user_id}")
            )
            profile = result.fetchone()
            
            if profile:
                print(f"\n❌ 错误: 创建了profile（不应该创建）")
                print(f"  - age_range: {profile[0]}")
                print(f"  - family_structure: {profile[1]}")
                print(f"  - occupation: {profile[2]}")
                
                if profile[0] == "30-40" or profile[1] == "single":
                    print(f"\n❌ 发现默认值！修复失败！")
                    return False
            else:
                print(f"\n✅ 正确: 没有创建profile（因为缺少必需字段）")
            
            break
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return False
    
    # 测试场景2: 提供年龄和家庭结构
    print("\n" + "=" * 80)
    print("场景2: 提供年龄和家庭结构")
    print("=" * 80)
    
    message_2 = "我35岁，已婚有孩子"
    print(f"\n用户消息: {message_2}")
    
    result = await extractor.extract_information(message_2)
    
    print(f"\n提取结果:")
    print(f"  - 年龄段: {result.get('risk_profile', {}).get('age_range')}")
    print(f"  - 家庭结构: {result.get('risk_profile', {}).get('family_structure')}")
    
    # 尝试更新用户状态
    success = await asset_extraction_service.update_user_state(user_id, result)
    print(f"\n更新用户状态: {'成功' if success else '失败'}")
    
    # 检查数据库中是否创建了profile
    async for db in get_db_session():
        try:
            result = await db.execute(
                text(f"SELECT age_range, family_structure FROM userprofile WHERE user_id = {user_id}")
            )
            profile = result.fetchone()
            
            if profile:
                print(f"\n✅ 正确: 创建了profile")
                print(f"  - age_range: {profile[0]}")
                print(f"  - family_structure: {profile[1]}")
                
                if profile[0] == "30-40" and profile[1] == "married_with_kids":
                    print(f"\n✅ 数据正确！修复成功！")
                    return True
                else:
                    print(f"\n❌ 数据不正确")
                    return False
            else:
                print(f"\n❌ 错误: 没有创建profile（应该创建）")
                return False
            
            break
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_no_default_values())
    
    print("\n" + "=" * 80)
    if result:
        print("✅ 所有测试通过！默认值问题已修复！")
    else:
        print("❌ 测试失败！")
    print("=" * 80)
