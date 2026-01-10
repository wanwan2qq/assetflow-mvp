#!/usr/bin/env python3
"""
测试前端编译状态的脚本
"""

import requests
import time

def test_frontend_compilation():
    """测试前端是否成功编译和启动"""
    
    print("🔧 测试前端编译状态")
    print("=" * 40)
    
    max_attempts = 30  # 最多等待30秒
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get("http://localhost:8080", timeout=2)
            if response.status_code == 200:
                print("✅ 前端编译成功，应用已启动")
                print(f"   状态码: {response.status_code}")
                print(f"   响应长度: {len(response.text)} 字符")
                return True
        except requests.exceptions.ConnectionError:
            print(f"⏳ 等待前端启动... ({attempt + 1}/{max_attempts})")
        except Exception as e:
            print(f"⚠️  请求异常: {e}")
        
        time.sleep(1)
        attempt += 1
    
    print("❌ 前端启动超时或编译失败")
    return False

def test_backend_status():
    """测试后端状态"""
    
    print("\n🔧 测试后端状态")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False

def main():
    """主测试函数"""
    
    print("🧪 前后端服务状态检查")
    print("=" * 50)
    
    # 测试后端
    backend_ok = test_backend_status()
    
    # 测试前端
    frontend_ok = test_frontend_compilation()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   后端服务: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"   前端编译: {'✅ 成功' if frontend_ok else '❌ 失败'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 所有服务正常运行！")
        print("📱 可以访问 http://localhost:8080 测试应用")
    else:
        print("\n⚠️  部分服务异常，请检查:")
        if not backend_ok:
            print("   - 确保后端服务已启动")
        if not frontend_ok:
            print("   - 检查前端编译错误")
            print("   - 查看Flutter控制台输出")

if __name__ == "__main__":
    main()