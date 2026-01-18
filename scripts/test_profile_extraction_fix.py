#!/usr/bin/env python3
"""
用户画像提取修复验证脚本
测试改进后的fallback模式和数据库外键约束修复
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_enhanced_fallback_extraction():
    """测试增强的fallback提取功能"""
    print("=" * 80)
    print("🧠 测试增强的Fallback用户画像提取")
    print("=" * 80)
    
    try:
        from app.services.information_extraction import InformationExtractor
        
        # 创建提取器实例（会自动进入fallback模式，因为没有OpenAI密钥）
        extractor = InformationExtractor()
        print(f"✅ InformationExtractor创建成功，LLM状态: {extractor.llm is not None}")
        
        # 测试用例：包含丰富用户信息的文本
        test_cases = [
            {
                "name": "完整用户信息",
                "text": "我今年32岁，已婚有孩子，是一名程序员，月收入2万，每月支出大概1.5万，比较保守，喜欢稳健的投资",
                "expected": {
                    "age_range": "30-40",
                    "family_structure": "married_with_kids", 
                    "occupation": "程序员",
                    "risk_preference": "conservative",
                    "monthly_expense": 15000.0
                }
            },
            {
                "name": "部分用户信息",
                "text": "我25岁，单身，比较激进，喜欢高风险高收益的投资",
                "expected": {
                    "age_range": "20-30",
                    "family_structure": "single",
                    "risk_preference": "aggressive"
                }
            },
            {
                "name": "年龄和家庭信息",
                "text": "我和老公结婚5年了，我今年28岁，我们有一个3岁的女儿",
                "expected": {
                    "age_range": "20-30",
                    "family_structure": "married_with_kids"
                }
            },
            {
                "name": "职业和收入信息", 
                "text": "我是医生，年收入大概50万，月支出2万左右",
                "expected": {
                    "occupation": "医生",
                    "income_range": "50万",
                    "monthly_expense": 20000.0
                }
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 测试用例 {i}: {test_case['name']}")
            print(f"   输入: {test_case['text']}")
            
            try:
                # 调用fallback提取
                assets, profile, validation = await extractor._fallback_extraction(test_case['text'])
                
                if profile:
                    print("   ✅ 成功提取用户画像:")
                    print(f"      - 年龄范围: {profile.age_range}")
                    print(f"      - 家庭结构: {profile.family_structure}")
                    print(f"      - 职业: {profile.occupation}")
                    print(f"      - 风险偏好: {profile.risk_preference}")
                    print(f"      - 月支出: {profile.monthly_expense}")
                    print(f"      - 收入范围: {profile.income_range}")
                    print(f"      - 置信度: {profile.confidence}")
                    
                    # 验证期望结果
                    matches = 0
                    total_expected = len(test_case['expected'])
                    
                    for key, expected_value in test_case['expected'].items():
                        actual_value = getattr(profile, key, None)
                        if actual_value == expected_value:
                            matches += 1
                            print(f"      ✅ {key}: {actual_value} (匹配)")
                        else:
                            print(f"      ❌ {key}: 期望 {expected_value}, 实际 {actual_value}")
                    
                    accuracy = matches / total_expected
                    print(f"      📊 准确率: {accuracy:.1%} ({matches}/{total_expected})")
                    
                    if accuracy >= 0.8:  # 80%以上准确率算成功
                        success_count += 1
                        print("      🎯 测试通过")
                    else:
                        print("      ⚠️ 准确率偏低")
                        
                else:
                    print("   ❌ 未提取到用户画像")
                    
            except Exception as e:
                print(f"   ❌ 提取失败: {e}")
        
        print(f"\n📊 总体结果: {success_count}/{len(test_cases)} 个测试用例通过")
        return success_count >= len(test_cases) * 0.75  # 75%通过率
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_database_foreign_key_fix():
    """测试数据库外键约束修复"""
    print("\n" + "=" * 80)
    print("💾 测试数据库外键约束修复")
    print("=" * 80)
    
    try:
        from app.services.asset_extraction_service import AssetExtractionService
        from app.core.database import get_db_session
        
        service = AssetExtractionService()
        print("✅ AssetExtractionService创建成功")
        
        # 测试1: 使用不存在的用户ID（应该优雅处理）
        print("\n📝 测试1: 不存在的用户ID (999999)")
        
        async for session in get_db_session():
            try:
                # 模拟提取到的用户画像数据
                mock_risk_profile = {
                    "age_range": "30-40",
                    "family_structure": "married_with_kids",
                    "tolerance": "moderate",
                    "occupation": "程序员",
                    "monthly_expense": 15000.0
                }
                
                await service._update_user_profile_from_extraction(
                    user_id=999999,
                    risk_profile=mock_risk_profile,
                    session=session
                )
                
                print("   ✅ 不存在用户ID处理成功（没有抛出异常）")
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                return False
            break
        
        # 测试2: 使用存在的用户ID
        print("\n📝 测试2: 存在的用户ID (1)")
        
        async for session in get_db_session():
            try:
                mock_risk_profile = {
                    "age_range": "30-40", 
                    "family_structure": "married_with_kids",
                    "tolerance": "moderate",
                    "occupation": "测试工程师",
                    "monthly_expense": 12000.0
                }
                
                await service._update_user_profile_from_extraction(
                    user_id=1,
                    risk_profile=mock_risk_profile,
                    session=session
                )
                
                # 提交更改
                await session.commit()
                print("   ✅ 存在用户ID处理成功")
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                return False
            break
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

async def test_end_to_end_extraction():
    """端到端提取测试"""
    print("\n" + "=" * 80)
    print("🔄 端到端用户画像提取测试")
    print("=" * 80)
    
    try:
        from app.services.information_extraction import InformationExtractor
        
        extractor = InformationExtractor()
        
        # 使用正确的方法签名
        test_message = "我今年35岁，已婚有两个孩子，是一名软件工程师，月收入3万，每月支出2万，比较稳健，不喜欢高风险投资"
        
        print(f"📝 测试消息: {test_message}")
        
        # 执行完整的提取流程（使用正确的方法签名）
        assets, profile, validation = await extractor.extract_information_from_conversation(
            text=test_message,
            conversation_history=[]
        )
        
        print("\n✅ 提取结果:")
        print(f"   - 提取的资产数量: {len(assets)}")
        print(f"   - 用户画像: {'是' if profile else '否'}")
        print(f"   - 验证状态: {validation.get('is_valid', False)}")
        print(f"   - 完整性评分: {validation.get('completeness_score', 0):.2f}")
        
        if profile:
            print(f"   - 年龄范围: {profile.age_range}")
            print(f"   - 家庭结构: {profile.family_structure}")
            print(f"   - 职业: {profile.occupation}")
            print(f"   - 风险偏好: {profile.risk_preference}")
            print(f"   - 月支出: {profile.monthly_expense}")
            print(f"   - 收入范围: {profile.income_range}")
        
        return profile is not None
        
    except Exception as e:
        print(f"❌ 端到端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有修复验证测试"""
    print("🚀 用户画像提取修复验证")
    print("测试增强的fallback模式和数据库外键约束修复")
    
    async def run_all_tests():
        results = []
        
        # 测试1: 增强的fallback提取
        result1 = await test_enhanced_fallback_extraction()
        results.append(("增强Fallback提取", result1))
        
        # 测试2: 数据库外键约束修复
        result2 = await test_database_foreign_key_fix()
        results.append(("数据库外键约束修复", result2))
        
        # 测试3: 端到端提取
        result3 = await test_end_to_end_extraction()
        results.append(("端到端提取测试", result3))
        
        return results
    
    # 运行异步测试
    results = asyncio.run(run_all_tests())
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 修复验证总结")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有修复验证通过！用户画像提取问题已解决")
        print("\n✅ 修复内容:")
        print("   1. 增强fallback模式，支持用户画像提取")
        print("   2. 添加数据库外键约束检查")
        print("   3. 改进错误处理和日志记录")
        print("   4. 支持多种中文表达模式")
    else:
        print(f"\n⚠️ 还有 {total - passed} 个问题需要解决")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())