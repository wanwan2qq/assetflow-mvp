#!/usr/bin/env python3
"""
Generate a fresh token for the frontend to fix the connection issue
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.auth import auth_service

def generate_fresh_token():
    """Generate a fresh token for user 9"""
    print("🔑 为用户9生成新的Token...")
    
    user_id = 9
    token = auth_service.create_access_token(user_id)
    
    print(f"✅ 新Token生成成功:")
    print(f"   用户ID: {user_id}")
    print(f"   Token: {token}")
    
    # Test the token
    try:
        verified_user_id = auth_service.verify_token(token)
        print(f"✅ Token验证成功，用户ID: {verified_user_id}")
    except Exception as e:
        print(f"❌ Token验证失败: {e}")
        return None
    
    print(f"\n📋 前端使用说明:")
    print(f"1. 打开浏览器开发者工具")
    print(f"2. 在Console中执行以下代码:")
    print(f"   localStorage.setItem('auth_token', '{token}');")
    print(f"3. 刷新页面")
    
    return token

if __name__ == "__main__":
    token = generate_fresh_token()
    if token:
        print(f"\n🎯 成功生成新Token，请按照上述说明更新前端Token")
    else:
        print(f"\n❌ Token生成失败")
        sys.exit(1)