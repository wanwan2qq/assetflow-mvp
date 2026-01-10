#!/usr/bin/env python3
"""
调试Token验证问题
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def debug_token_verification():
    """调试Token验证"""
    
    try:
        from app.services.auth import auth_service
        
        # 测试token生成和验证
        user_id = 9
        
        print("🔐 Token生成和验证调试")
        print("=" * 40)
        print()
        
        # 生成token
        print("1. 生成Token...")
        token = auth_service.create_access_token(user_id)
        print(f"   Token: {token[:50]}...")
        print()
        
        # 立即验证token
        print("2. 验证Token...")
        verified_user_id = auth_service.verify_token(token)
        print(f"   验证结果: {verified_user_id}")
        
        if verified_user_id == user_id:
            print("   ✅ Token验证成功")
        elif verified_user_id is None:
            print("   ❌ Token验证失败：返回None")
        else:
            print(f"   ❌ Token验证失败：用户ID不匹配 (期望: {user_id}, 实际: {verified_user_id})")
        
        print()
        
        # 检查auth_service的配置
        print("3. 检查auth_service配置...")
        print(f"   SECRET_KEY存在: {hasattr(auth_service, 'secret_key')}")
        if hasattr(auth_service, 'secret_key'):
            print(f"   SECRET_KEY长度: {len(auth_service.secret_key)}")
        
        return verified_user_id == user_id
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_token_verification()
    
    if not success:
        print()
        print("💡 可能的问题:")
        print("   1. SECRET_KEY配置问题")
        print("   2. JWT库版本问题")
        print("   3. Token格式问题")
        print("   4. 时间同步问题")