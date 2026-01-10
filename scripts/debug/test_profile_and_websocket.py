#!/usr/bin/env python3
"""
测试个人中心和WebSocket功能的脚本
"""

import requests
import json
import asyncio
import websockets
import time

def test_user_profile_api():
    """测试用户个人信息API"""
    
    print("👤 测试用户个人信息API")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1"
    test_phone = "13444444444"
    
    # 1. 发送验证码并登录获取token
    try:
        # 发送验证码
        response = requests.post(
            f"{base_url}/auth/send-sms",
            json={"phone": test_phone},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 发送验证码失败: {response.text}")
            return None
            
        print("✅ 验证码已发送，请查看后端控制台")
        verification_code = input("请输入验证码: ").strip()
        
        if not verification_code:
            print("❌ 未输入验证码")
            return None
        
        # 登录获取token
        response = requests.post(
            f"{base_url}/auth/login/phone",
            json={
                "phone": test_phone,
                "verification_code": verification_code
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 登录失败: {response.text}")
            return None
            
        auth_data = response.json()
        token = auth_data['access_token']
        user_id = auth_data['user_id']
        
        print(f"✅ 登录成功，用户ID: {user_id}")
        
        # 2. 测试获取用户信息
        response = requests.get(
            f"{base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 用户信息获取成功:")
            print(f"   ID: {user_info['id']}")
            print(f"   手机号: {user_info['phone']}")
            print(f"   设备ID: {user_info.get('device_id', 'None')}")
            print(f"   创建时间: {user_info['created_at']}")
            
            return {"token": token, "user_id": user_id, "user_info": user_info}
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return None

async def test_websocket_connection(user_id, token):
    """测试WebSocket连接"""
    
    print(f"\n🔌 测试WebSocket连接")
    print("=" * 40)
    
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    print(f"WebSocket URL: {websocket_url}")
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待欢迎消息
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 收到欢迎消息: {welcome_msg}")
            except asyncio.TimeoutError:
                print("⚠️  未收到欢迎消息")
            
            # 发送测试消息
            test_message = {
                "type": "message",
                "content": "你好，这是一个测试消息"
            }
            
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            print(f"📤 发送测试消息: {test_message['content']}")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"📨 收到响应: {response}")
                return True
            except asyncio.TimeoutError:
                print("⚠️  响应超时")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False

def test_anonymous_user():
    """测试匿名用户功能"""
    
    print(f"\n👻 测试匿名用户功能")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1"
    test_device_id = f"test-device-{int(time.time())}"
    
    try:
        # 匿名登录
        response = requests.post(
            f"{base_url}/auth/login/device",
            json={"device_id": test_device_id},
            timeout=10
        )
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"✅ 匿名登录成功:")
            print(f"   用户ID: {auth_data['user_id']}")
            print(f"   匿名手机号: {auth_data['phone']}")
            print(f"   设备ID: {auth_data['device_id']}")
            
            return {
                "token": auth_data['access_token'],
                "user_id": auth_data['user_id'],
                "phone": auth_data['phone'],
                "device_id": auth_data['device_id']
            }
        else:
            print(f"❌ 匿名登录失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 匿名登录异常: {e}")
        return None

async def main():
    """主测试函数"""
    
    print("🧪 个人中心和WebSocket功能测试")
    print("=" * 50)
    
    # 测试1: 手机号登录用户
    print("📱 测试场景1: 手机号登录用户")
    user_data = test_user_profile_api()
    
    if user_data:
        # 测试WebSocket连接
        websocket_success = await test_websocket_connection(
            user_data["user_id"], 
            user_data["token"]
        )
        
        print(f"\n📊 手机号用户测试结果:")
        print(f"   登录: ✅ 成功")
        print(f"   个人信息: ✅ 成功")
        print(f"   WebSocket: {'✅ 成功' if websocket_success else '❌ 失败'}")
    
    # 测试2: 匿名用户
    print(f"\n👻 测试场景2: 匿名用户")
    anonymous_data = test_anonymous_user()
    
    if anonymous_data:
        # 测试WebSocket连接
        websocket_success = await test_websocket_connection(
            anonymous_data["user_id"], 
            anonymous_data["token"]
        )
        
        print(f"\n📊 匿名用户测试结果:")
        print(f"   匿名登录: ✅ 成功")
        print(f"   WebSocket: {'✅ 成功' if websocket_success else '❌ 失败'}")
    
    print("\n" + "=" * 50)
    print("🎯 前端测试指南:")
    print("1. 访问 http://localhost:8080")
    print("2. 使用手机号登录或匿名体验")
    print("3. 检查个人中心是否显示正确的用户信息")
    print("4. 检查聊天页面是否显示'已连接到AI助手'")
    print("5. 尝试发送消息测试AI对话功能")

if __name__ == "__main__":
    asyncio.run(main())