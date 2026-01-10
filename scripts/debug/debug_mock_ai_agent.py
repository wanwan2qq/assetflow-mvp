#!/usr/bin/env python3
"""
调试Mock AI代理问题
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_mock_ai_agent():
    """测试Mock AI代理"""
    
    print("🤖 测试Mock AI代理")
    print("=" * 50)
    
    try:
        from app.services.chat_agent import get_chat_agent
        
        # 获取聊天代理
        agent = get_chat_agent()
        
        print(f"📋 AI代理信息:")
        print(f"   OpenAI API Key: {agent.openai_api_key[:20]}...")
        print(f"   Has Real OpenAI Key: {agent.has_real_openai_key}")
        print(f"   Agent Type: {'Real' if agent.has_real_openai_key else 'Mock'}")
        print()
        
        # 测试消息处理
        user_id = 9
        test_message = "你好"
        
        print(f"📤 发送测试消息: '{test_message}'")
        print(f"👤 用户ID: {user_id}")
        print()
        
        print("🔄 处理消息...")
        response_chunks = []
        
        async for chunk in agent.process_message(test_message, user_id, None):
            response_chunks.append(chunk)
            print(f"📨 收到chunk: '{chunk.strip()}'")
        
        full_response = "".join(response_chunks)
        print()
        print(f"✅ 完整响应: '{full_response}'")
        print(f"📊 响应长度: {len(full_response)} 字符")
        print(f"📊 Chunk数量: {len(response_chunks)}")
        
        if full_response.strip():
            print("✅ Mock AI代理工作正常")
            return True
        else:
            print("❌ Mock AI代理返回空响应")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_message_flow():
    """测试WebSocket消息流程"""
    
    print()
    print("🔌 测试WebSocket消息流程")
    print("=" * 50)
    
    try:
        # 模拟WebSocket消息处理流程
        from app.services.chat_agent import get_chat_agent
        import json
        
        agent = get_chat_agent()
        user_id = 9
        user_message = "你好"
        
        print(f"1. 📤 用户发送消息: '{user_message}'")
        
        # 模拟typing消息
        typing_msg = {
            "type": "typing",
            "content": "AI正在思考中...",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        print(f"2. ⌨️  发送typing消息: {typing_msg}")
        
        # 处理AI消息
        print("3. 🤖 处理AI消息...")
        response_chunks = []
        
        async for chunk in agent.process_message(user_message, user_id, None):
            if chunk.strip():
                response_chunks.append(chunk)
                
                # 模拟chunk消息
                chunk_msg = {
                    "type": "chunk",
                    "content": chunk,
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                print(f"   📨 Chunk消息: {chunk_msg}")
        
        # 模拟complete消息
        full_response = "".join(response_chunks)
        
        # 提取UI组件
        ui_components = agent.extract_ui_components(full_response)
        
        complete_msg = {
            "type": "complete",
            "content": full_response,
            "ui_components": [comp.model_dump() for comp in ui_components],
            "timestamp": "2024-01-01T00:00:00Z",
        }
        print(f"4. ✅ Complete消息: {complete_msg}")
        
        if response_chunks:
            print("✅ WebSocket消息流程正常")
            return True
        else:
            print("❌ WebSocket消息流程异常：没有响应chunks")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    
    # 测试Mock AI代理
    ai_success = await test_mock_ai_agent()
    
    # 测试WebSocket消息流程
    ws_success = await test_websocket_message_flow()
    
    print()
    print("📊 测试结果总结:")
    print(f"   Mock AI代理: {'✅ 正常' if ai_success else '❌ 异常'}")
    print(f"   WebSocket流程: {'✅ 正常' if ws_success else '❌ 异常'}")
    
    if ai_success and ws_success:
        print()
        print("💡 如果测试正常但前端没有收到响应，可能的原因:")
        print("   1. 前端消息处理逻辑问题")
        print("   2. WebSocket消息格式问题")
        print("   3. 前端状态更新问题")
        print("   4. 后端日志记录问题")
    else:
        print()
        print("💡 需要检查:")
        print("   1. Mock AI代理的实现")
        print("   2. 消息处理异常")
        print("   3. 后端配置问题")

if __name__ == "__main__":
    asyncio.run(main())