#!/usr/bin/env python3
"""
实时调试WebSocket通信
"""

import asyncio
import websockets
import json
import sys

async def debug_websocket_communication():
    """实时调试WebSocket通信"""
    
    # 使用新生成的有效token
    user_id = 9
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzY4NjQ1NzY2LCJpYXQiOjE3Njc5NTQ1NjYsInR5cGUiOiJhY2Nlc3MiLCJqd2kiOiIxNzY3OTI1NzY2LjcxOTQyIn0.8wd7Xe-Kw-XZrNy3WcG811JGOOWehPfkWBMUF1ZKJ_w"
    
    uri = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    print(f"🔌 连接WebSocket: {uri}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待欢迎消息
            print("⏳ 等待欢迎消息...")
            welcome_msg = await websocket.recv()
            print(f"📨 收到欢迎消息: {welcome_msg}")
            print()
            
            # 发送测试消息
            test_message = {
                "content": "你好",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            print(f"📤 发送测试消息: {test_message}")
            await websocket.send(json.dumps(test_message))
            print("✅ 消息已发送")
            print()
            
            # 监听响应消息
            print("👂 监听AI响应...")
            message_count = 0
            
            try:
                while message_count < 10:  # 最多等待10条消息
                    message = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    message_count += 1
                    
                    print(f"📨 消息 #{message_count}: {message}")
                    
                    # 解析消息
                    try:
                        msg_data = json.loads(message)
                        msg_type = msg_data.get('type')
                        msg_content = msg_data.get('content', '')
                        
                        print(f"   类型: {msg_type}")
                        print(f"   内容: {msg_content[:100]}{'...' if len(msg_content) > 100 else ''}")
                        
                        # 如果是complete消息，说明响应完成
                        if msg_type == 'complete':
                            print("✅ AI响应完成")
                            break
                            
                    except json.JSONDecodeError:
                        print(f"   原始消息: {message}")
                    
                    print()
                    
            except asyncio.TimeoutError:
                print("⏰ 等待响应超时")
                
            print(f"📊 总共收到 {message_count} 条消息")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket连接关闭: {e}")
    except Exception as e:
        print(f"❌ WebSocket错误: {e}")

async def main():
    """主函数"""
    
    print("🐛 实时WebSocket通信调试")
    print("=" * 60)
    print()
    
    await debug_websocket_communication()

if __name__ == "__main__":
    asyncio.run(main())