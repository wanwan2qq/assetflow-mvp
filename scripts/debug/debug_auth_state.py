#!/usr/bin/env python3
"""
调试认证状态的脚本
"""

import requests
import json

def test_login_and_profile():
    """测试登录后的用户状态"""
    
    print("🔍 调试认证状态")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1"
    test_phone = "13777777777"
    
    # 1. 发送验证码
    print(f"📱 1. 发送验证码到 {test_phone}")
    response = requests.post(
        f"{base_url}/auth/send-sms",
        json={"phone": test_phone},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ 发送验证码失败: {response.text}")
        return
    
    print("✅ 验证码已发送，请查看后端控制台")
    verification_code = input("请输入验证码: ").strip()
    
    if not verification_code:
        print("❌ 未输入验证码")
        return
    
    # 2. 登录
    print(f"\n🔐 2. 使用验证码 {verification_code} 登录")
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
        return
    
    auth_data = response.json()
    token = auth_data['access_token']
    user_id = auth_data['user_id']
    
    print(f"✅ 登录成功!")
    print(f"   用户ID: {user_id}")
    print(f"   手机号: {auth_data['phone']}")
    print(f"   Token: {token[:50]}...")
    
    # 3. 验证token有效性
    print(f"\n👤 3. 验证Token有效性")
    response = requests.get(
        f"{base_url}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"✅ Token有效，用户信息:")
        print(f"   ID: {user_info['id']}")
        print(f"   手机号: {user_info['phone']}")
        print(f"   设备ID: {user_info.get('device_id', 'None')}")
        print(f"   创建时间: {user_info['created_at']}")
        
        # 4. 分析用户类型
        print(f"\n🔍 4. 分析用户类型")
        phone = user_info['phone']
        device_id = user_info.get('device_id')
        
        if device_id is not None:
            print(f"   用户类型: 匿名用户 (有设备ID)")
            print(f"   设备ID: {device_id}")
        else:
            print(f"   用户类型: 手机号用户 (无设备ID)")
        
        # 检查是否为生成的匿名手机号
        if phone.startswith('1') and len(phone) == 11:
            try:
                int(phone)
                print(f"   手机号类型: 可能是生成的匿名手机号")
            except ValueError:
                print(f"   手机号类型: 真实手机号")
        
        return {
            "token": token,
            "user_info": user_info,
            "is_anonymous": device_id is not None
        }
    else:
        print(f"❌ Token验证失败: {response.text}")
        return None

def main():
    """主函数"""
    
    print("🧪 认证状态调试")
    print("=" * 50)
    
    result = test_login_and_profile()
    
    if result:
        print("\n" + "=" * 50)
        print("📊 调试结果:")
        print(f"   Token有效: ✅")
        print(f"   用户类型: {'匿名用户' if result['is_anonymous'] else '手机号用户'}")
        print(f"   手机号: {result['user_info']['phone']}")
        
        print("\n🔧 前端调试建议:")
        print("1. 检查浏览器开发者工具的Console面板")
        print("2. 查看是否有'🔍 个人中心'开头的调试日志")
        print("3. 确认AuthState和Token的值")
        print("4. 检查是否有页面跳转时的状态重置")
        
        print(f"\n📱 测试Token:")
        print(f"Bearer {result['token']}")

if __name__ == "__main__":
    main()