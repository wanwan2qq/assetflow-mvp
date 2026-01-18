"""
测试收入提取滞后问题

检查为什么收入更新比其他信息更新滞后
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.information_extraction import InformationExtractor


async def test_income_extraction():
    """测试收入提取"""
    
    print("=" * 80)
    print("测试：收入提取诊断")
    print("=" * 80)
    
    extractor = InformationExtractor()
    
    # 测试场景1: 提供年收入
    print("\n" + "=" * 80)
    print("场景1: 用户提供年收入")
    print("=" * 80)
    
    message_1 = "我年收入50万"
    print(f"\n用户消息: {message_1}")
    
    result = await extractor.extract_information(message_1)
    
    print(f"\n提取结果:")
    print(f"  risk_profile: {result.get('risk_profile', {})}")
    
    income_range = result.get('risk_profile', {}).get('income_range')
    print(f"\n  - income_range: {income_range}")
    
    if income_range:
        print(f"  ✅ 成功提取收入范围")
    else:
        print(f"  ❌ 未提取到收入范围")
    
    # 测试场景2: 提供月收入
    print("\n" + "=" * 80)
    print("场景2: 用户提供月收入")
    print("=" * 80)
    
    message_2 = "我月收入3万"
    print(f"\n用户消息: {message_2}")
    
    result = await extractor.extract_information(message_2)
    
    print(f"\n提取结果:")
    print(f"  risk_profile: {result.get('risk_profile', {})}")
    
    income_range = result.get('risk_profile', {}).get('income_range')
    print(f"\n  - income_range: {income_range}")
    
    if income_range:
        print(f"  ✅ 成功提取收入范围")
    else:
        print(f"  ❌ 未提取到收入范围")
    
    # 测试场景3: 同时提供年龄和收入
    print("\n" + "=" * 80)
    print("场景3: 同时提供年龄和收入")
    print("=" * 80)
    
    message_3 = "我35岁，年收入50万"
    print(f"\n用户消息: {message_3}")
    
    result = await extractor.extract_information(message_3)
    
    print(f"\n提取结果:")
    print(f"  risk_profile: {result.get('risk_profile', {})}")
    
    age_range = result.get('risk_profile', {}).get('age_range')
    income_range = result.get('risk_profile', {}).get('income_range')
    
    print(f"\n  - age_range: {age_range}")
    print(f"\n  - income_range: {income_range}")
    
    if age_range:
        print(f"  ✅ 成功提取年龄")
    else:
        print(f"  ❌ 未提取到年龄")
    
    if income_range:
        print(f"  ✅ 成功提取收入")
    else:
        print(f"  ❌ 未提取到收入")
    
    # 测试场景4: 检查fallback提取
    print("\n" + "=" * 80)
    print("场景4: 测试fallback提取")
    print("=" * 80)
    
    message_4 = "我年收入大概50万"
    print(f"\n用户消息: {message_4}")
    
    assets, profile, validation = await extractor._fallback_extraction(message_4)
    
    print(f"\nFallback提取结果:")
    if profile:
        print(f"  - income_range: {profile.income_range}")
        if profile.income_range:
            print(f"  ✅ Fallback成功提取收入")
        else:
            print(f"  ❌ Fallback未提取到收入")
    else:
        print(f"  ❌ Fallback未创建profile")
    
    # 分析问题
    print("\n" + "=" * 80)
    print("问题分析")
    print("=" * 80)
    
    print("\n可能的原因:")
    print("  1. LLM提取时，prompt中没有明确的收入提取规则")
    print("  2. LLM返回的JSON中可能使用了 'monthly_income' 而不是 'income_range'")
    print("  3. Fallback提取的正则表达式可能不够全面")
    print("  4. 收入字段可能被其他字段覆盖或忽略")
    
    print("\n建议修复:")
    print("  1. 在 profile_extraction.yaml 中添加明确的收入提取规则")
    print("  2. 处理 'monthly_income' 字段并转换为 'income_range'")
    print("  3. 增强fallback提取的正则表达式")
    print("  4. 添加日志跟踪收入提取的每个步骤")


if __name__ == "__main__":
    asyncio.run(test_income_extraction())
