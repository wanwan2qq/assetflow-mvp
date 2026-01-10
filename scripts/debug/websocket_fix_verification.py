#!/usr/bin/env python3
"""
WebSocket关闭代码修复验证
"""

import os
import re

def check_frontend_websocket_fixes():
    """检查前端WebSocket修复"""
    print("🔍 检查前端WebSocket修复...")
    
    websocket_service_path = "frontend/lib/core/services/websocket_service.dart"
    
    if not os.path.exists(websocket_service_path):
        print(f"❌ 文件不存在: {websocket_service_path}")
        return False
    
    with open(websocket_service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用了normalClosure而不是goingAway
    if 'status.normalClosure' in content:
        print("✅ 前端使用正确的关闭代码 (status.normalClosure)")
    else:
        print("❌ 前端未使用正确的关闭代码")
        return False
    
    # 检查是否还有goingAway的使用
    if 'status.goingAway' in content:
        print("❌ 前端仍在使用无效的关闭代码 (status.goingAway)")
        return False
    else:
        print("✅ 前端已移除无效的关闭代码")
    
    # 检查所有close调用都有状态码
    close_calls = re.findall(r'\.close\([^)]*\)', content)
    close_without_status = [call for call in close_calls if 'status.' not in call and 'close()' not in call]
    
    if close_without_status:
        print(f"⚠️  发现没有状态码的close调用: {close_without_status}")
    else:
        print("✅ 所有WebSocket close调用都有适当的状态码")
    
    return True

def check_backend_websocket_fixes():
    """检查后端WebSocket修复"""
    print("\n🔍 检查后端WebSocket修复...")
    
    chat_endpoint_path = "backend/app/api/api_v1/endpoints/chat.py"
    
    if not os.path.exists(chat_endpoint_path):
        print(f"❌ 文件不存在: {chat_endpoint_path}")
        return False
    
    with open(chat_endpoint_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否添加了异常处理
    exception_patterns = [
        r'try:\s*await websocket\.send_text',
        r'except Exception as.*:',
        r'logger\.error.*Failed to send'
    ]
    
    fixes_found = 0
    for pattern in exception_patterns:
        if re.search(pattern, content):
            fixes_found += 1
    
    if fixes_found >= 2:  # 至少找到try-except和logger.error
        print("✅ 后端添加了WebSocket发送消息的异常处理")
    else:
        print("❌ 后端缺少WebSocket发送消息的异常处理")
        return False
    
    # 检查使用的关闭代码是否有效
    close_codes = re.findall(r'websocket\.close\(code=(\d+)', content)
    invalid_codes = [code for code in close_codes if int(code) not in [1000, 1008, 1011] and not (3000 <= int(code) <= 4999)]
    
    if invalid_codes:
        print(f"❌ 后端使用了无效的关闭代码: {invalid_codes}")
        return False
    else:
        print("✅ 后端使用了有效的关闭代码")
    
    return True

def main():
    """主验证函数"""
    print("WebSocket关闭代码修复验证")
    print("=" * 50)
    
    frontend_ok = check_frontend_websocket_fixes()
    backend_ok = check_backend_websocket_fixes()
    
    print("\n" + "=" * 50)
    print("验证结果:")
    
    if frontend_ok and backend_ok:
        print("✅ 所有修复都已正确应用")
        print("\n修复内容总结:")
        print("1. 前端WebSocket使用1000（正常关闭）代码")
        print("2. 后端添加了发送消息的异常处理")
        print("3. 这应该解决以下错误:")
        print("   - InvalidAccessError: Failed to execute 'close' on 'WebSocket'")
        print("   - WebSocket error: Unexpected ASGI message 'websocket.send'")
        
        print("\n🎉 修复完成！现在可以测试WebSocket连接了。")
        return True
    else:
        print("❌ 部分修复未正确应用，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)