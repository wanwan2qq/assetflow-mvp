#!/usr/bin/env python3
"""
专门诊断用户画像提取问题的脚本
深入分析为什么用户信息没有更新
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_profile_extraction_step_by_step():
    """逐步测试profile提取的每个环节"""
    print("=" * 80)
    print("🔍 逐步诊断用户画像提取问题")
    print("=" * 80)
    
    # 测试用例
    test_messages = [
        "我今年30岁，已婚有孩子，月收入2万，月支出1万5",
        "我是程序员，比较保守，不喜欢高风险投资",
        "我90后，单身，做销售工作，每月花费8000左右"
    ]
    
    try:
        from app.services.information_extraction import information_extractor
        
        print(f"✅ InformationExtractor导入成功")
        print(f"   - 有效OpenAI密钥: {information_extractor.has_real_openai_key}")
        print(f"   - LLM实例: {information_extractor.llm is not None}")
        
        if not information_extractor.has_real_openai_key:
            print("⚠️  警告: 没有有效的OpenAI API密钥，将使用fallback模式")
            print("   fallback模式不会提取用户画像信息！")
            return False
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 测试用例 {i}: {message}")
            
            # 步骤1: 测试完整提取
            print("   步骤1: 完整信息提取...")
            try:
                assets, profile, validation = await information_extractor.extract_information_from_conversation(message)
                print(f"   ✅ 完整提取成功")
                print(f"      - 资产数量: {len(assets)}")
                print(f"      - 用户画像: {profile is not None}")
                print(f"      - 验证结果: {validation.get('intent', 'unknown')}")
                
                if profile:
                    print(f"      - 年龄范围: {profile.age_range}")
                    print(f"      - 家庭结构: {profile.family_structure}")
                    print(f"      - 月支出: {profile.monthly_expense}")
                    print(f"      - 风险偏好: {profile.risk_preference}")
                    print(f"      - 职业: {profile.occupation}")
                    print(f"      - 收入范围: {profile.income_range}")
                else:
                    print("      ❌ 没有提取到用户画像")
                
            except Exception as e:
                print(f"   ❌ 完整提取失败: {e}")
                continue
            
            # 步骤2: 测试单独的profile提取
            print("   步骤2: 单独profile提取...")
            try:
                profile_only = await information_extractor._extract_profile(message, [])
                print(f"   ✅ 单独profile提取: {profile_only is not None}")
                
                if profile_only:
                    print(f"      - 提取来源: {profile_only.extracted_from}")
                    print(f"      - 置信度: {profile_only.confidence}")
                else:
                    print("      ❌ 单独profile提取也失败")
                
            except Exception as e:
                print(f"   ❌ 单独profile提取失败: {e}")
                continue
            
            # 步骤3: 测试prompt构建
            print("   步骤3: 测试prompt构建...")
            try:
                prompt = information_extractor._build_profile_extraction_prompt(message, [])
                print(f"   ✅ Prompt构建成功，长度: {len(prompt)} 字符")
                print(f"      前100字符: {prompt[:100]}...")
                
            except Exception as e:
                print(f"   ❌ Prompt构建失败: {e}")
                continue
            
            # 步骤4: 测试LLM调用（如果有真实API密钥）
            if information_extractor.llm:
                print("   步骤4: 测试LLM调用...")
                try:
                    response = await information_extractor.llm.ainvoke(prompt)
                    print(f"   ✅ LLM调用成功")
                    print(f"      响应长度: {len(response.content)} 字符")
                    print(f"      响应内容: {response.content[:200]}...")
                    
                    # 尝试解析JSON
                    try:
                        result = json.loads(response.content)
                        print(f"   ✅ JSON解析成功")
                        print(f"      Profile数据: {result.get('profile', {})}")
                    except json.JSONDecodeError as je:
                        print(f"   ❌ JSON解析失败: {je}")
                        print(f"      原始响应: {response.content}")
                    
                except Exception as e:
                    print(f"   ❌ LLM调用失败: {e}")
                    continue
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_extract_information_function():
    """测试extract_information函数"""
    print("\n" + "=" * 80)
    print("🧪 测试extract_information函数")
    print("=" * 80)
    
    try:
        from app.services.information_extraction import extract_information
        
        test_message = "我今年35岁，已婚有孩子，是程序员，月收入3万，月支出2万"
        conversation_history = []
        
        print(f"测试消息: {test_message}")
        
        result = await extract_information(test_message, conversation_history)
        
        print(f"✅ extract_information调用成功")
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 检查关键字段
        risk_profile = result.get("risk_profile", {})
        if risk_profile:
            print(f"✅ 找到risk_profile数据:")
            for key, value in risk_profile.items():
                print(f"   - {key}: {value}")
        else:
            print(f"❌ 没有risk_profile数据")
        
        return result
        
    except Exception as e:
        print(f"❌ extract_information测试失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")
        return None

async def test_database_update():
    """测试数据库更新逻辑"""
    print("\n" + "=" * 80)
    print("💾 测试数据库更新逻辑")
    print("=" * 80)
    
    try:
        from app.services.asset_extraction_service import asset_extraction_service
        
        # 模拟提取结果
        mock_extraction_result = {
            "assets": [],
            "goals": ["buy_house"],
            "risk_profile": {
                "age_range": "30-35",
                "family_structure": "married_with_kids",
                "tolerance": "moderate",
                "monthly_expense": 20000,
                "occupation": "程序员",
                "income_range": "20000-30000"
            },
            "completeness_update": {},
            "intent": "new_info"
        }
        
        print(f"模拟提取结果: {json.dumps(mock_extraction_result, ensure_ascii=False, indent=2)}")
        
        # 测试用户ID（使用一个测试ID）
        test_user_id = 999999
        
        print(f"测试用户ID: {test_user_id}")
        
        # 调用更新函数
        success = await asset_extraction_service.update_user_state(test_user_id, mock_extraction_result)
        
        print(f"✅ 数据库更新结果: {success}")
        
        return success
        
    except Exception as e:
        print(f"❌ 数据库更新测试失败: {e}")
        import traceback
        print(f"   错误详情: {traceback.format_exc()}")
        return False

async def test_fallback_mode():
    """测试fallback模式的行为"""
    print("\n" + "=" * 80)
    print("🔄 测试Fallback模式")
    print("=" * 80)
    
    try:
        from app.services.information_extraction import information_extractor
        
        # 强制进入fallback模式
        original_llm = information_extractor.llm
        information_extractor.llm = None
        
        test_message = "我今年30岁，已婚有孩子，月收入2万"
        
        print(f"测试消息: {test_message}")
        print("强制使用fallback模式...")
        
        assets, profile, validation = await information_extractor.extract_information_from_conversation(test_message)
        
        print(f"Fallback模式结果:")
        print(f"   - 资产数量: {len(assets)}")
        print(f"   - 用户画像: {profile is not None}")
        print(f"   - 验证结果: {validation}")
        
        # 恢复原始LLM
        information_extractor.llm = original_llm
        
        if profile is None:
            print("❌ 确认: Fallback模式不提取用户画像")
            return False
        else:
            print("✅ Fallback模式也能提取用户画像")
            return True
        
    except Exception as e:
        print(f"❌ Fallback模式测试失败: {e}")
        return False

async def main():
    """运行所有诊断测试"""
    print("🚀 用户画像提取问题深度诊断")
    print("开始逐步排查问题...")
    
    results = []
    
    # 测试1: 逐步profile提取
    print("\n" + "🔍" * 20)
    result1 = await test_profile_extraction_step_by_step()
    results.append(("逐步Profile提取", result1))
    
    # 测试2: extract_information函数
    print("\n" + "🧪" * 20)
    result2 = await test_extract_information_function()
    results.append(("extract_information函数", result2 is not None))
    
    # 测试3: 数据库更新
    print("\n" + "💾" * 20)
    result3 = await test_database_update()
    results.append(("数据库更新", result3))
    
    # 测试4: fallback模式
    print("\n" + "🔄" * 20)
    result4 = await test_fallback_mode()
    results.append(("Fallback模式", result4))
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 诊断总结")
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
        print("🎉 所有测试通过 - 用户画像提取应该正常工作")
        return 0
    else:
        print("⚠️  发现问题 - 需要修复以下问题:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))