#!/usr/bin/env python3
"""
生成有效的JWT token用于测试
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def generate_token():
    """生成有效的JWT token"""
    
    try:
        from app.services.auth import auth_service
        
        # 为用户ID 9生成token
        user_id = 9
        token = auth_service.create_access_token(user_id)
        
        print(f"🔑 为用户ID {user_id} 生成新token:")
        print(f"Token: {token}")
        print()
        
        # 验证token
        verified_user_id = auth_service.verify_token(token)
        
        if verified_user_id == user_id:
            print("✅ Token验证成功")
            print(f"验证结果: 用户ID {verified_user_id}")
        else:
            print("❌ Token验证失败")
            print(f"期望用户ID: {user_id}")
            print(f"验证结果: {verified_user_id}")
        
        return token
        
    except Exception as e:
        print(f"❌ 生成token失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔐 JWT Token生成器")
    print("=" * 40)
    print()
    
    token = generate_token()
    
    if token:
        print()
        print("💡 使用方法:")
        print("1. 复制上面的token")
        print("2. 在前端重新登录或手动设置token")
        print("3. 测试WebSocket连接")