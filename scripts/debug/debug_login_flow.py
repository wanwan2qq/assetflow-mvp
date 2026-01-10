#!/usr/bin/env python3
"""
调试登录流程的脚本
"""

import requests
import json

def debug_login_flow():
    """调试完整的登录流程"""
    
    base_url = "http://localhost:8000/api/v1"
    test_phone = "13666666666"
    
    print("🔍 调试登录流程")
    print("=" * 40)
    
    # 1. 发送验证码
    print(f"📱 1. 发送验证码到 {test_phone}")
    try:
        response = requests.post(
            f"{base_url}/auth/send-sms",
            json={"phone": test_phone},
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
        
        if response.status_code != 200:
            print("❌ 发送验证码失败")
            return
            
    except Exception as e:
        print(f"❌ 发送验证码异常: {e}")
        return
    
    # 2. 提示用户输入验证码
    print("\n🔢 2. 请查看后端控制台输出的验证码")
    verification_code = input("请输入验证码: ").strip()
    
    if not verification_code:
        print("❌ 未输入验证码")
        return
    
    # 3. 测试登录
    print(f"\n🔐 3. 使用验证码 {verification_code} 登录")
    try:
        response = requests.post(
            f"{base_url}/auth/login/phone",
            json={
                "phone": test_phone,
                "verification_code": verification_code
            },
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应体: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功!")
            print(f"   用户ID: {result.get('user_id')}")
            print(f"   手机号: {result.get('phone')}")
            print(f"   Token: {result.get('access_token', '')[:50]}...")
            
            # 4. 测试获取用户信息
            print(f"\n👤 4. 测试获取用户信息")
            token = result.get('access_token')
            if token:
                user_response = requests.get(
                    f"{base_url}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                print(f"   用户信息状态码: {user_response.status_code}")
                print(f"   用户信息: {user_response.text}")
        else:
            print("❌ 登录失败")
            
    except Exception as e:
        print(f"❌ 登录异常: {e}")

if __name__ == "__main__":
    debug_login_flow()