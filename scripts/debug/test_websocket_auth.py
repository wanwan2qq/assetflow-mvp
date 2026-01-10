#!/usr/bin/env python3
"""
测试WebSocket认证函数
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_auth():
    """测试WebSocket认证函数"""
    
    try:
        from app.api.api_v1.endpoints.chat import authenticate_websocket
        
        # 使用新生成的有效token
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzY4NjQ1NzY2LCJpYXQiOjE3Njc5NTQ1NjYsInR5cGUiOiJhY2Nlc3MiLCJqd2kiOiIxNzY3OTI1NzY2LjcxOTQyIn0.8wd7Xe-Kw-XZrNy3WcG811JGOOWehPfkWBMUF1ZKJ_w"
        
        print(f"🔑 测试WebSocket认证")
        print(f"Token: {token[:50]}...")
        print()
        
        user = await authenticate_websocket(token)
        
        print(f"✅ 认证成功:")
        print(f"   用户ID: {user.id}")
        print(f"   手机号: {user.phone}")
        
        return True
        
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔐 WebSocket认证测试")
    print("=" * 40)
    print()
    
    success = asyncio.run(test_websocket_auth())
    
    if success:
        print()
        print("💡 认证函数正常，WebSocket连接问题可能在其他地方")
    else:
        print()
        print("💡 认证函数有问题，需要修复")