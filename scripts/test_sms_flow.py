#!/usr/bin/env python3
"""
测试SMS验证码完整流程的脚本
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_sms_flow():
    """测试完整的SMS验证码流程"""
    
    print("🧪 开始测试SMS验证码流程")
    print("=" * 50)
    
    # 测试手机号
    test_phone = "13812345678"
    
    # 1. 发送验证码
    print(f"📱 1. 发送验证码到 {test_phone}")
    response = requests.post(
        f"{BASE_URL}/auth/send-sms",
        json={"phone": test_phone}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 验证码发送成功: {result['message']}")
    else:
        print(f"❌ 验证码发送失败: {response.text}")
        return
    
    # 提示用户查看控制台
    print("\n🔍 请查看后端服务控制台输出，找到验证码")
    verification_code = input("请输入看到的验证码: ").strip()
    
    if not verification_code:
        print("❌ 未输入验证码，测试结束")
        return
    
    # 2. 使用验证码登录
    print(f"\n🔐 2. 使用验证码 {verification_code} 登录")
    response = requests.post(
        f"{BASE_URL}/auth/login/phone",
        json={
            "phone": test_phone,
            "verification_code": verification_code
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登录成功!")
        print(f"   用户ID: {result['user_id']}")
        print(f"   手机号: {result['phone']}")
        print(f"   Token: {result['access_token'][:50]}...")
        
        # 保存token用于后续测试
        token = result['access_token']
        
        # 3. 测试获取用户信息
        print(f"\n👤 3. 获取用户信息")
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ 用户信息获取成功:")
            print(f"   ID: {user_info['id']}")
            print(f"   手机号: {user_info['phone']}")
            print(f"   设备ID: {user_info.get('device_id', 'None')}")
            print(f"   创建时间: {user_info['created_at']}")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
            
    else:
        print(f"❌ 登录失败: {response.text}")
        return
    
    # 4. 测试频率限制
    print(f"\n⏱️  4. 测试频率限制 (再次发送验证码)")
    response = requests.post(
        f"{BASE_URL}/auth/send-sms",
        json={"phone": test_phone}
    )
    
    if response.status_code == 429:
        print(f"✅ 频率限制正常工作: {response.json()['detail']}")
    else:
        print(f"⚠️  频率限制可能有问题: {response.text}")
    
    # 5. 测试设备登录
    print(f"\n📱 5. 测试设备ID登录")
    test_device_id = "test-device-sms-flow-123"
    response = requests.post(
        f"{BASE_URL}/auth/login/device",
        json={"device_id": test_device_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 设备登录成功!")
        print(f"   用户ID: {result['user_id']}")
        print(f"   设备ID: {result['device_id']}")
        print(f"   匿名手机号: {result['phone']}")
    else:
        print(f"❌ 设备登录失败: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 SMS验证码流程测试完成!")

if __name__ == "__main__":
    try:
        test_sms_flow()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保服务已启动在 http://localhost:8000")
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")