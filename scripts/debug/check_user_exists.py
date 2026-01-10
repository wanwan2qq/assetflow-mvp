#!/usr/bin/env python3
"""
检查用户是否存在于数据库中
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def check_user_exists():
    """检查用户是否存在"""
    
    try:
        from sqlmodel import select
        from app.core.database import get_db_session
        from app.models.user import User
        
        user_id = 9
        
        print(f"🔍 检查用户ID {user_id} 是否存在...")
        
        async for session in get_db_session():
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"✅ 用户存在:")
                print(f"   ID: {user.id}")
                print(f"   手机号: {user.phone}")
                print(f"   创建时间: {user.created_at}")
                return True
            else:
                print(f"❌ 用户ID {user_id} 不存在")
                
                # 列出所有用户
                all_users_statement = select(User)
                all_users_result = await session.execute(all_users_statement)
                all_users = all_users_result.scalars().all()
                
                print(f"📋 数据库中的所有用户:")
                for u in all_users:
                    print(f"   ID: {u.id}, 手机号: {u.phone}")
                
                return False
                
    except Exception as e:
        print(f"❌ 检查用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("👤 用户存在性检查")
    print("=" * 30)
    print()
    
    asyncio.run(check_user_exists())