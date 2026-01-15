#!/usr/bin/env python3
"""
局域网访问诊断脚本
检查前端和后端服务的局域网访问配置
"""

import requests
import subprocess
import sys
from urllib.parse import urlparse


def get_local_ip():
    """获取本机IP地址"""
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'inet ' in line and '127.0.0.1' not in line:
                parts = line.strip().split()
                for i, part in enumerate(parts):
                    if part == 'inet' and i + 1 < len(parts):
                        ip = parts[i + 1]
                        if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                            return ip
        return None
    except Exception as e:
        print(f"❌ 获取IP地址失败: {e}")
        return None


def check_backend_service(ip, port=8000):
    """检查后端服务是否可访问"""
    urls_to_check = [
        f"http://localhost:{port}/health",
        f"http://{ip}:{port}/health"
    ]
    
    print(f"\n🔍 检查后端服务 (端口 {port}):")
    print("-" * 50)
    
    for url in urls_to_check:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - 正常 (状态码: {response.status_code})")
            else:
                print(f"⚠️  {url} - 异常 (状态码: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - 连接失败 (服务未启动)")
        except requests.exceptions.Timeout:
            print(f"❌ {url} - 超时")
        except Exception as e:
            print(f"❌ {url} - 错误: {e}")


def check_cors_config(ip, port=8000):
    """检查CORS配置"""
    print(f"\n🔍 检查CORS配置:")
    print("-" * 50)
    
    # 模拟跨域请求
    headers = {
        'Origin': f'http://{ip}:8080',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options(f"http://{ip}:{port}/api/v1/health/", headers=headers, timeout=5)
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        
        if cors_headers:
            print("✅ CORS 头部存在:")
            for header, value in cors_headers.items():
                print(f"   {header}: {value}")
        else:
            print("❌ 未找到 CORS 头部")
            
    except Exception as e:
        print(f"❌ CORS 检查失败: {e}")


def check_frontend_service(ip, port=8080):
    """检查前端服务是否可访问"""
    urls_to_check = [
        f"http://localhost:{port}",
        f"http://{ip}:{port}"
    ]
    
    print(f"\n🔍 检查前端服务 (端口 {port}):")
    print("-" * 50)
    
    for url in urls_to_check:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # 检查是否是空白页面
                content_length = len(response.text.strip())
                if content_length > 1000:  # 正常页面应该有足够内容
                    print(f"✅ {url} - 正常 (内容长度: {content_length})")
                else:
                    print(f"⚠️  {url} - 可能是空白页面 (内容长度: {content_length})")
            else:
                print(f"⚠️  {url} - 异常 (状态码: {response.status_code})")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - 连接失败 (服务未启动)")
        except requests.exceptions.Timeout:
            print(f"❌ {url} - 超时")
        except Exception as e:
            print(f"❌ {url} - 错误: {e}")


def check_network_connectivity(ip):
    """检查网络连通性"""
    print(f"\n🔍 检查网络连通性:")
    print("-" * 50)
    
    try:
        # Ping 测试
        result = subprocess.run(['ping', '-c', '1', ip], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Ping {ip} - 成功")
        else:
            print(f"❌ Ping {ip} - 失败")
    except Exception as e:
        print(f"❌ Ping 测试失败: {e}")


def provide_solutions():
    """提供解决方案"""
    print(f"\n💡 解决方案:")
    print("=" * 50)
    print("1. 启动后端服务:")
    print("   cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("")
    print("2. 启动前端服务:")
    print("   cd frontend && flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0")
    print("")
    print("3. 检查防火墙设置:")
    print("   - 确保 8000 和 8080 端口开放")
    print("   - macOS: 系统偏好设置 > 安全性与隐私 > 防火墙")
    print("")
    print("4. 如果仍然白屏，检查浏览器控制台:")
    print("   - 按 F12 打开开发者工具")
    print("   - 查看 Console 和 Network 标签页的错误信息")


def main():
    print("🔍 AssetFlow 局域网访问诊断工具")
    print("=" * 50)
    
    # 获取本机IP
    local_ip = get_local_ip()
    if not local_ip:
        print("❌ 无法获取本机IP地址")
        sys.exit(1)
    
    print(f"📍 检测到本机IP: {local_ip}")
    
    # 检查各项服务
    check_backend_service(local_ip)
    check_cors_config(local_ip)
    check_frontend_service(local_ip)
    check_network_connectivity(local_ip)
    
    # 提供解决方案
    provide_solutions()
    
    print(f"\n🌐 推荐访问地址:")
    print(f"   前端: http://{local_ip}:8080/#/login")
    print(f"   后端: http://{local_ip}:8000/docs")


if __name__ == "__main__":
    main()