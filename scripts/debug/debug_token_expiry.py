#!/usr/bin/env python3
"""
调试Token过期问题
"""

import base64
import json
from datetime import datetime

def decode_token_info(token):
    """解码JWT token信息"""
    
    print(f"🔍 分析Token: {token[:50]}...")
    print()
    
    try:
        # JWT token由三部分组成，用.分隔
        parts = token.split('.')
        
        if len(parts) != 3:
            print(f"❌ Token格式错误: 应该有3部分，实际有{len(parts)}部分")
            return None
        
        print(f"📋 Token结构: {len(parts[0])}字符.{len(parts[1])}字符.{len(parts[2])}字符")
        
        # 解码payload (第二部分)
        payload = parts[1]
        
        # 添加padding如果需要
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # Base64解码
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_json = json.loads(decoded_bytes.decode('utf-8'))
        
        print("📋 Token内容:")
        for key, value in decoded_json.items():
            if key == 'exp':
                # 转换过期时间
                exp_time = datetime.fromtimestamp(value)
                current_time = datetime.now()
                is_expired = current_time > exp_time
                
                print(f"   {key}: {value} ({exp_time})")
                print(f"   当前时间: {current_time}")
                print(f"   是否过期: {'是' if is_expired else '否'}")
                
                if is_expired:
                    expired_duration = current_time - exp_time
                    print(f"   过期时长: {expired_duration}")
                else:
                    remaining_time = exp_time - current_time
                    print(f"   剩余时间: {remaining_time}")
            else:
                print(f"   {key}: {value}")
        
        return decoded_json
        
    except Exception as e:
        print(f"❌ Token解码失败: {e}")
        return None

def main():
    """主函数"""
    
    print("🔑 Token过期问题调试")
    print("=" * 50)
    print()
    
    # 从日志中看到的token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5IiwiZXhwIjoxNzM2NTI1MjEyfQ.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    
    decoded = decode_token_info(token)
    
    if decoded:
        print()
        print("💡 解决方案:")
        
        exp_timestamp = decoded.get('exp', 0)
        current_timestamp = datetime.now().timestamp()
        
        if current_timestamp > exp_timestamp:
            print("   1. Token已过期，需要重新登录")
            print("   2. 或者实现token自动刷新机制")
            print("   3. 检查前端是否有token刷新逻辑")
        else:
            print("   1. Token未过期，检查其他认证问题")
            print("   2. 检查用户ID是否匹配")
            print("   3. 检查后端认证逻辑")
    else:
        print()
        print("💡 Token格式问题:")
        print("   1. Token格式不正确")
        print("   2. Token可能被截断或损坏")
        print("   3. 需要重新获取有效token")

if __name__ == "__main__":
    main()