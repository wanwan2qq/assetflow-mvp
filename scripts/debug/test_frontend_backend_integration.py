#!/usr/bin/env python3
"""
测试前后端SMS验证码集成的脚本
"""

import requests
import time
import json

def test_backend_sms_api():
    """测试后端SMS API是否正常工作"""
    
    print("🔧 测试后端SMS API")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1"
    test_phone = "13888888888"
    
    # 1. 测试健康检查
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        return False
    
    # 2. 测试发送验证码API
    try:
        response = requests.post(
            f"{base_url}/auth/send-sms",
            json={"phone": test_phone},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 发送验证码API正常: {result['message']}")
        else:
            print(f"❌ 发送验证码API失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 发送验证码API异常: {e}")
        return False
    
    # 3. 测试设备登录API
    try:
        response = requests.post(
            f"{base_url}/auth/login/device",
            json={"device_id": "test-integration-device"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 设备登录API正常: 用户ID {result['user_id']}")
            return True
        else:
            print(f"❌ 设备登录API失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 设备登录API异常: {e}")
        return False

def test_frontend_accessibility():
    """测试前端是否可访问"""
    
    print("\n🌐 测试前端可访问性")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:8080", timeout=10)
        if response.status_code == 200:
            print("✅ 前端服务运行正常 (http://localhost:8080)")
            return True
        else:
            print(f"❌ 前端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务 (http://localhost:8080)")
        print("   请确保前端已启动: flutter run -d chrome --web-port 8080")
        return False
    except Exception as e:
        print(f"❌ 前端服务异常: {e}")
        return False

def check_cors_configuration():
    """检查CORS配置"""
    
    print("\n🔒 检查CORS配置")
    print("=" * 40)
    
    try:
        # 模拟前端发起的预检请求
        response = requests.options(
            "http://localhost:8000/api/v1/auth/send-sms",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=5
        )
        
        cors_headers = response.headers
        if "Access-Control-Allow-Origin" in cors_headers:
            print(f"✅ CORS配置正常: {cors_headers.get('Access-Control-Allow-Origin')}")
            return True
        else:
            print("⚠️  CORS配置可能有问题，前端可能无法访问后端API")
            return False
    except Exception as e:
        print(f"❌ CORS检查异常: {e}")
        return False

def main():
    """主测试函数"""
    
    print("🧪 前后端SMS验证码集成测试")
    print("=" * 50)
    
    # 测试后端API
    backend_ok = test_backend_sms_api()
    
    # 测试前端可访问性
    frontend_ok = test_frontend_accessibility()
    
    # 检查CORS配置
    cors_ok = check_cors_configuration()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   后端API: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"   前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"   CORS配置: {'✅ 正常' if cors_ok else '⚠️  需检查'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 集成测试通过！")
        print("\n📝 测试步骤:")
        print("1. 打开浏览器访问: http://localhost:8080")
        print("2. 输入手机号: 13888888888")
        print("3. 点击'发送验证码'按钮")
        print("4. 查看后端控制台输出的验证码")
        print("5. 输入验证码并点击'登录'")
        
        if not cors_ok:
            print("\n⚠️  注意: CORS配置可能需要调整")
    else:
        print("\n❌ 集成测试失败，请检查服务状态")
        
        if not backend_ok:
            print("   - 确保后端服务已启动: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        if not frontend_ok:
            print("   - 确保前端服务已启动: flutter run -d chrome --web-port 8080")

if __name__ == "__main__":
    main()