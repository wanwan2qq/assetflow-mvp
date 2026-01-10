#!/usr/bin/env python3
"""
测试仪表盘修复的脚本
"""

import requests
import json

def test_dashboard_api():
    """测试仪表盘相关的API"""
    
    print("🧪 仪表盘API测试")
    print("=" * 40)
    
    # 1. 获取认证token
    print("📱 1. 获取认证Token")
    response = requests.post('http://localhost:8000/api/v1/auth/login/device', 
                           json={'device_id': 'test-dashboard-fix'})
    
    if response.status_code != 200:
        print(f"❌ 获取Token失败: {response.text}")
        return False
        
    data = response.json()
    token = data['access_token']
    user_id = data['user_id']
    print(f"✅ Token获取成功: 用户ID {user_id}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. 测试资产列表API
    print(f"\n📊 2. 测试资产列表API")
    response = requests.get(f'http://localhost:8000/api/v1/assets/{user_id}', headers=headers)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        assets = response.json()
        print(f"✅ 资产列表获取成功: {len(assets.get('data', []))} 个资产")
    else:
        print(f"❌ 资产列表获取失败: {response.text}")
    
    # 3. 测试投资组合健康度API
    print(f"\n💊 3. 测试投资组合健康度API")
    response = requests.get(f'http://localhost:8000/api/v1/assets/{user_id}/portfolio/health', headers=headers)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        portfolio_data = response.json()
        print(f"✅ 投资组合健康度获取成功")
        
        # 验证数据结构
        if 'data' in portfolio_data:
            data_section = portfolio_data['data']
            print(f"   净资产: {data_section.get('net_worth', 0)} 元")
            print(f"   房产占比: {data_section.get('real_estate_ratio', 0) * 100:.1f}%")
            print(f"   流动性比率: {data_section.get('liquidity_ratio', 0):.1f}")
            print(f"   风险警告: {len(data_section.get('risk_warnings', []))} 条")
            
            # 检查数据类型
            net_worth = data_section.get('net_worth')
            real_estate_ratio = data_section.get('real_estate_ratio')
            liquidity_ratio = data_section.get('liquidity_ratio')
            
            print(f"\\n   数据类型验证:")
            print(f"   net_worth: {type(net_worth)} = {net_worth}")
            print(f"   real_estate_ratio: {type(real_estate_ratio)} = {real_estate_ratio}")
            print(f"   liquidity_ratio: {type(liquidity_ratio)} = {liquidity_ratio}")
            
            # 检查是否有null值
            has_null = any(v is None for v in [net_worth, real_estate_ratio, liquidity_ratio])
            if has_null:
                print("❌ 发现null值，这可能导致前端类型错误")
                return False
            else:
                print("✅ 所有数值字段都不为null")
                
        return True
    else:
        print(f"❌ 投资组合健康度获取失败: {response.text}")
        return False

def test_add_sample_asset():
    """添加示例资产来测试非空数据"""
    
    print(f"\n🏠 4. 添加示例资产")
    
    # 获取token
    response = requests.post('http://localhost:8000/api/v1/auth/login/device', 
                           json={'device_id': 'test-add-asset'})
    
    if response.status_code != 200:
        print(f"❌ 获取Token失败")
        return False
        
    data = response.json()
    token = data['access_token']
    user_id = data['user_id']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 添加房产资产
    asset_data = {
        "asset_type": "real_estate",
        "name": "测试房产",
        "value": 5000000,  # 500万
        "is_confirmed": True,
        "metadata": {
            "area": 120,
            "location": "北京市朝阳区"
        }
    }
    
    response = requests.post(f'http://localhost:8000/api/v1/assets/{user_id}', 
                           json=asset_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ 示例房产添加成功")
        
        # 再次获取投资组合健康度
        response = requests.get(f'http://localhost:8000/api/v1/assets/{user_id}/portfolio/health', headers=headers)
        if response.status_code == 200:
            portfolio_data = response.json()
            data_section = portfolio_data['data']
            print(f"   更新后净资产: {data_section.get('net_worth', 0)} 元")
            print(f"   更新后房产占比: {data_section.get('real_estate_ratio', 0) * 100:.1f}%")
            return True
    else:
        print(f"❌ 添加资产失败: {response.text}")
        return False

def main():
    """主测试函数"""
    
    print("🎯 仪表盘修复验证")
    print("=" * 50)
    
    # 测试基础API
    api_success = test_dashboard_api()
    
    # 测试添加资产
    asset_success = test_add_sample_asset()
    
    print("\\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   基础API: {'✅ 正常' if api_success else '❌ 异常'}")
    print(f"   资产功能: {'✅ 正常' if asset_success else '❌ 异常'}")
    
    if api_success and asset_success:
        print("\\n🎉 仪表盘功能修复成功!")
        print("📱 前端仪表盘现在应该能正常显示数据")
    else:
        print("\\n⚠️  仍有问题需要进一步调试")
    
    return api_success and asset_success

if __name__ == "__main__":
    result = main()
    exit(0 if result else 1)