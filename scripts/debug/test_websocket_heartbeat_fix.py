#!/usr/bin/env python3
"""
测试WebSocket心跳消息处理修复
"""

import asyncio
import json
import websockets
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_heartbeat():
    """测试WebSocket心跳消息不会触发消息格式错误"""
    
    # 这里需要一个有效的token，从环境变量或配置文件获取
    # 为了测试，我们先模拟一下
    user_id = 9  # 使用测试用户ID
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzM2NTI1MjEyfQ.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # 需要有效token
    
    uri = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        print(f"🔌 连接到WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待欢迎消息
            welcome_msg = await websocket.recv()
            print(f"📨 收到欢迎消息: {welcome_msg}")
            
            # 发送心跳消息
            print("💓 发送心跳消息: ping")
            await websocket.send("ping")
            
            # 等待心跳响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"💓 收到心跳响应: {response}")
            
            if response == "pong":
                print("✅ 心跳消息处理正常")
            else:
                print(f"❌ 心跳响应异常: {response}")
                # 检查是否是错误消息
                try:
                    error_data = json.loads(response)
                    if error_data.get("type") == "error" and "消息格式错误" in error_data.get("content", ""):
                        print("❌ 心跳消息仍然触发消息格式错误")
                        return False
                except json.JSONDecodeError:
                    pass
            
            # 发送正常聊天消息测试
            chat_message = {
                "content": "你好",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            print(f"💬 发送聊天消息: {chat_message}")
            await websocket.send(json.dumps(chat_message))
            
            # 等待AI响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"🤖 收到AI响应: {response[:100]}...")
            
            return True
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket连接关闭: {e}")
        return False
    except asyncio.TimeoutError:
        print("❌ 等待响应超时")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 开始测试WebSocket心跳消息处理修复...")
    
    success = await test_websocket_heartbeat()
    
    if success:
        print("✅ 测试通过：心跳消息处理修复成功")
        return 0
    else:
        print("❌ 测试失败：心跳消息处理仍有问题")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)