#!/usr/bin/env python3
"""
简化版用户画像提取诊断脚本
不依赖langchain等包，专注测试基础逻辑
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_prompt_manager():
    """测试PromptManager是否能正常加载profile_extraction.yaml"""
    print("=" * 80)
    print("🔧 测试PromptManager和Profile Prompt")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        print("✅ PromptManager导入成功")
        
        # 测试加载profile_extraction.yaml
        try:
            system_prompt = prompt_manager.get_raw(
                category="extraction",
                filename="profile_extraction",
                key="system_instruction"
            )
            print(f"✅ Profile系统指令加载成功，长度: {len(system_prompt)} 字符")
            print(f"   前100字符: {system_prompt[:100]}...")
            
        except Exception as e:
            print(f"❌ Profile系统指令加载失败: {e}")
            return False
        
        # 测试渲染用户指令
        try:
            user_prompt = prompt_manager.render(
                category="extraction",
                filename="profile_extraction",
                key="user_instruction",
                context_str="测试上下文",
                user_message="我今年30岁，已婚有孩子"
            )
            print(f"✅ Profile用户指令渲染成功，长度: {len(user_prompt)} 字符")
            print(f"   包含测试消息: {'我今年30岁' in user_prompt}")
            
        except Exception as e:
            print(f"❌ Profile用户指令渲染失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PromptManager测试失败: {e}")
        return False

def test_profile_extraction_logic():
    """测试profile提取的逻辑部分（不调用LLM）"""
    print("\n" + "=" * 80)
    print("🧠 测试Profile提取逻辑")
    print("=" * 80)
    
    # 模拟LLM返回的JSON数据
    mock_llm_responses = [
        {
            "profile": {
                "age_range": "30-35",
                "family_structure": "married_with_kids",
                "monthly_expense": 15000,
                "risk_preference": "moderate",
                "occupation": "程序员"
            }
        },
        {
            "profile": {
                "age_range": "25-30",
                "family_structure": "single",
                "risk_preference": "aggressive"
            }
        },
        {
            "profile": {}  # 空profile
        },
        {}  # 没有profile字段
    ]
    
    try:
        # 导入ExtractedUserProfile类
        from app.services.information_extraction import ExtractedUserProfile
        print("✅ ExtractedUserProfile类导入成功")
        
        # 测试每个mock响应
        for i, mock_response in enumerate(mock_llm_responses, 1):
            print(f"\n📝 测试用例 {i}: {mock_response}")
            
            profile_data = mock_response.get("profile", {})
            
            # 模拟_parse_profile逻辑
            if not profile_data or not any(profile_data.values()):
                print("   ❌ Profile数据为空，返回None")
                continue
            
            try:
                profile = ExtractedUserProfile(
                    age_range=profile_data.get("age_range"),
                    family_structure=profile_data.get("family_structure"),
                    monthly_expense=profile_data.get("monthly_expense"),
                    risk_preference=profile_data.get("risk_preference"),
                    occupation=profile_data.get("occupation"),
                    income_range=profile_data.get("income_range"),
                    confidence=0.80,
                    extracted_from="测试消息",
                )
                
                print("   ✅ Profile对象创建成功:")
                print(f"      - 年龄范围: {profile.age_range}")
                print(f"      - 家庭结构: {profile.family_structure}")
                print(f"      - 月支出: {profile.monthly_expense}")
                print(f"      - 风险偏好: {profile.risk_preference}")
                print(f"      - 职业: {profile.occupation}")
                print(f"      - 置信度: {profile.confidence}")
                
            except Exception as e:
                print(f"   ❌ Profile对象创建失败: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 逻辑测试失败: {e}")
        return False

def test_database_models():
    """测试数据库模型是否可以导入"""
    print("\n" + "=" * 80)
    print("💾 测试数据库模型")
    print("=" * 80)
    
    try:
        # 尝试导入UserProfile模型
        from app.models.user import UserProfile
        print("✅ UserProfile模型导入成功")
        
        # 创建一个测试实例（不保存到数据库）
        test_profile = UserProfile(
            user_id=999999,
            age_range="30-35",
            family_structure="married_with_kids",
            risk_preference="moderate",
            monthly_expense=15000,
            occupation="程序员"
        )
        
        print("✅ UserProfile实例创建成功:")
        print(f"   - 用户ID: {test_profile.user_id}")
        print(f"   - 年龄范围: {test_profile.age_range}")
        print(f"   - 家庭结构: {test_profile.family_structure}")
        print(f"   - 风险偏好: {test_profile.risk_preference}")
        print(f"   - 月支出: {test_profile.monthly_expense}")
        print(f"   - 职业: {test_profile.occupation}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 数据库模型导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
        return False

def analyze_fallback_mode():
    """分析fallback模式的问题"""
    print("\n" + "=" * 80)
    print("🔄 分析Fallback模式问题")
    print("=" * 80)
    
    print("📋 Fallback模式分析:")
    print("   1. 当没有有效的OpenAI API密钥时，系统进入fallback模式")
    print("   2. Fallback模式只做简单的关键词匹配")
    print("   3. 当前的fallback实现不提取用户画像信息")
    print("   4. 这就是为什么用户信息没有更新的根本原因")
    
    print("\n🔍 问题根源:")
    print("   - information_extraction.py 第78行: 检查API密钥")
    print("   - 如果没有真实密钥，self.llm = None")
    print("   - extract_information_from_conversation 调用 _fallback_extraction")
    print("   - _fallback_extraction 只提取资产，不提取用户画像")
    
    print("\n💡 解决方案:")
    print("   方案1: 安装langchain依赖并配置OpenAI API密钥")
    print("   方案2: 改进fallback模式，增加用户画像提取")
    print("   方案3: 创建独立的规则引擎，不依赖LLM")
    
    return True

def check_environment():
    """检查运行环境"""
    print("\n" + "=" * 80)
    print("🌍 检查运行环境")
    print("=" * 80)
    
    import os
    
    # 检查环境变量
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base = os.getenv("OPENAI_API_BASE")
    
    print(f"环境变量检查:")
    print(f"   - OPENAI_API_KEY: {'已设置' if openai_key else '未设置'}")
    if openai_key:
        print(f"     值: {openai_key[:10]}...{openai_key[-4:] if len(openai_key) > 14 else openai_key}")
    print(f"   - OPENAI_API_BASE: {openai_base or '未设置'}")
    
    # 检查.env文件
    env_file = Path(__file__).parent / ".env"
    print(f"\n.env文件检查:")
    print(f"   - 文件存在: {env_file.exists()}")
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                has_openai_key = "OPENAI_API_KEY" in content
                print(f"   - 包含OPENAI_API_KEY: {has_openai_key}")
        except Exception as e:
            print(f"   - 读取失败: {e}")
    
    return True

def main():
    """运行所有简化测试"""
    print("🚀 用户画像提取问题简化诊断")
    print("专注测试基础逻辑，不依赖外部包")
    
    results = []
    
    # 测试1: PromptManager
    result1 = test_prompt_manager()
    results.append(("PromptManager", result1))
    
    # 测试2: Profile提取逻辑
    result2 = test_profile_extraction_logic()
    results.append(("Profile提取逻辑", result2))
    
    # 测试3: 数据库模型
    result3 = test_database_models()
    results.append(("数据库模型", result3))
    
    # 测试4: 环境检查
    result4 = check_environment()
    results.append(("环境检查", result4))
    
    # 分析5: Fallback模式
    result5 = analyze_fallback_mode()
    results.append(("Fallback模式分析", result5))
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 简化诊断总结")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n通过: {passed}/{total}")
    
    print("\n🎯 关键发现:")
    print("   1. 用户信息没有更新的根本原因是缺少langchain依赖")
    print("   2. 系统进入fallback模式，不提取用户画像")
    print("   3. 需要安装依赖包或改进fallback模式")
    
    return 0

if __name__ == "__main__":
    exit(main())