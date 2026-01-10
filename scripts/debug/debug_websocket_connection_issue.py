#!/usr/bin/env python3
"""
调试WebSocket连接一直显示"连接中"的问题
"""

import asyncio
import websockets
import json
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_connection():
    """测试WebSocket连接问题"""
    
    # 从日志中看到的token
    user_id = 9
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzM2NTI1MjEyfQ.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    
    uri = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    print(f"🔍 调试WebSocket连接问题")
    print(f"🔗 连接URI: {uri}")
    print(f"👤 用户ID: {user_id}")
    print(f"🔑 Token: {token[:50]}...")
    print()
    
    try:
        print("🔌 尝试建立WebSocket连接...")
        
        # 设置较短的超时来快速检测问题
        async with websockets.connect(uri, timeout=5) as websocket:
            print("✅ WebSocket连接建立成功")
            
            # 等待欢迎消息
            print("⏳ 等待欢迎消息...")
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 收到欢迎消息: {welcome_msg}")
                
                # 解析消息
                try:
                    msg_data = json.loads(welcome_msg)
                    print(f"📋 消息类型: {msg_data.get('type')}")
                    print(f"📝 消息内容: {msg_data.get('content')}")
                    
                    if msg_data.get('type') == 'system':
                        print("✅ 欢迎消息正常，连接应该成功")
                        return True
                    else:
                        print(f"⚠️ 意外的消息类型: {msg_data.get('type')}")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ 消息JSON解析失败: {e}")
                    print(f"📄 原始消息: {welcome_msg}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ 等待欢迎消息超时 - 可能是认证失败")
                return False
                
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket连接被拒绝: {e}")
        print("💡 可能的原因:")
        print("   - Token无效或过期")
        print("   - 用户ID不匹配")
        print("   - 后端认证逻辑问题")
        return False
        
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket连接被关闭: {e}")
        return False
        
    except asyncio.TimeoutError:
        print("❌ WebSocket连接超时")
        print("💡 可能的原因:")
        print("   - 后端服务未运行")
        print("   - 网络连接问题")
        print("   - 防火墙阻止连接")
        return False
        
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        print(f"🔍 错误类型: {type(e).__name__}")
        return False

async def test_token_validity():
    """测试Token有效性"""
    
    print("🔑 测试Token有效性...")
    
    # 使用curl测试Token
    import subprocess
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzM2NTI1MjEyfQ.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    
    try:
        # 测试用户信息API
        result = subprocess.run([
            'curl', '-s', '-w', '%{http_code}',
            '-H', f'Authorization: Bearer {token}',
            'http://localhost:8000/api/v1/auth/me'
        ], capture_output=True, text=True, timeout=10)
        
        # 分离响应体和状态码
        response_text = result.stdout
        if len(response_text) >= 3:
            status_code = response_text[-3:]
            response_body = response_text[:-3]
        else:
            status_code = response_text
            response_body = ""
        
        print(f"📊 HTTP状态码: {status_code}")
        
        if status_code == "200":
            print("✅ Token有效")
            if response_body:
                try:
                    import json
                    user_data = json.loads(response_body)
                    print(f"👤 用户: {user_data.get('phone', 'unknown')}")
                    print(f"🆔 用户ID: {user_data.get('id')}")
                except:
                    print(f"📄 响应: {response_body[:100]}...")
            return True
        elif status_code == "401":
            print("❌ Token无效或过期")
            print(f"📄 错误详情: {response_body}")
            return False
        else:
            print(f"⚠️ 意外的响应状态: {status_code}")
            print(f"📄 响应: {response_body}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ Token验证失败: {e}")
        return False

async def main():
    """主调试函数"""
    
    print("🐛 WebSocket连接问题调试")
    print("=" * 50)
    print()
    
    # 1. 测试Token有效性
    token_valid = await test_token_validity()
    print()
    
    if not token_valid:
        print("💡 建议:")
        print("   1. 检查用户是否正确登录")
        print("   2. 检查Token是否过期")
        print("   3. 重新登录获取新Token")
        return
    
    # 2. 测试WebSocket连接
    connection_success = await test_websocket_connection()
    print()
    
    if connection_success:
        print("✅ WebSocket连接正常")
        print("💡 前端连接问题可能是:")
        print("   1. 前端连接状态判断逻辑问题")
        print("   2. 消息处理逻辑问题")
        print("   3. 状态更新时机问题")
    else:
        print("❌ WebSocket连接有问题")
        print("💡 需要检查:")
        print("   1. 后端WebSocket认证逻辑")
        print("   2. Token格式和有效性")
        print("   3. 用户权限设置")

if __name__ == "__main__":
    asyncio.run(main())