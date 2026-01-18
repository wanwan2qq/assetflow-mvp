#!/usr/bin/env python3
"""
诊断脚本：检查模块化信息提取系统是否正常工作
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def diagnose_prompt_files():
    """诊断prompt文件是否存在且可加载"""
    print("=" * 80)
    print("🔍 诊断Prompt文件")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        # 检查模块化prompt文件
        modular_prompts = [
            ("asset_extraction", "资产提取"),
            ("profile_extraction", "用户画像提取"),
            ("intent_detection", "意图检测"),
            ("risk_assessment", "风险评估"),
            ("unified_extraction", "统一提取")
        ]
        
        all_good = True
        
        for filename, description in modular_prompts:
            try:
                system_prompt = prompt_manager.get_raw(
                    category="extraction",
                    filename=filename,
                    key="system_instruction"
                )
                print(f"✅ {description}: {len(system_prompt)} 字符")
                
                # 测试用户指令渲染
                user_prompt = prompt_manager.render(
                    category="extraction",
                    filename=filename,
                    key="user_instruction",
                    context_str="测试上下文",
                    user_message="测试消息",
                    user_profile="{}",
                    current_assets="[]"
                )
                print(f"   模板渲染: ✅")
                
            except Exception as e:
                print(f"❌ {description}: {e}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ PromptManager导入失败: {e}")
        return False

def diagnose_config_files():
    """诊断配置文件是否存在且可加载"""
    print("\n" + "=" * 80)
    print("🔧 诊断配置文件")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        config_files = [
            ("asset_type_mapping", "资产类型映射"),
            ("sp_quadrant_config", "SP四象限配置"),
            ("risk_assessment_rules", "风险评估规则")
        ]
        
        all_good = True
        
        for config_name, description in config_files:
            try:
                config_data = prompt_manager.get_config(config_name)
                print(f"✅ {description}: {len(config_data)} 顶级键")
                
            except Exception as e:
                print(f"❌ {description}: {e}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return False

def diagnose_information_extractor():
    """诊断InformationExtractor是否可以正常初始化"""
    print("\n" + "=" * 80)
    print("🧪 诊断InformationExtractor")
    print("=" * 80)
    
    try:
        from app.services.information_extraction import InformationExtractor
        
        # 创建实例
        extractor = InformationExtractor()
        print("✅ InformationExtractor实例创建成功")
        
        # 检查LLM状态
        if extractor.has_real_openai_key:
            print("✅ 检测到真实的OpenAI API密钥")
        else:
            print("⚠️  使用模拟模式（无真实OpenAI API密钥）")
        
        return True
        
    except Exception as e:
        print(f"❌ InformationExtractor初始化失败: {e}")
        return False

def diagnose_imports():
    """诊断关键模块导入是否正常"""
    print("\n" + "=" * 80)
    print("📦 诊断模块导入")
    print("=" * 80)
    
    imports = [
        ("app.core.prompt_manager", "PromptManager"),
        ("app.services.information_extraction", "信息提取服务"),
        ("app.services.chat_agent", "聊天代理"),
    ]
    
    all_good = True
    
    for module_name, description in imports:
        try:
            __import__(module_name)
            print(f"✅ {description}: 导入成功")
        except Exception as e:
            print(f"❌ {description}: {e}")
            all_good = False
    
    return all_good

def main():
    """运行所有诊断"""
    print("🚀 模块化信息提取系统诊断")
    print("检查重启后的系统状态")
    
    results = []
    
    # 运行诊断
    results.append(("模块导入", diagnose_imports()))
    results.append(("Prompt文件", diagnose_prompt_files()))
    results.append(("配置文件", diagnose_config_files()))
    results.append(("InformationExtractor", diagnose_information_extractor()))
    
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
        print("🎉 所有诊断通过 - 系统运行正常！")
        return 0
    else:
        print("⚠️  发现问题 - 请检查上述错误信息")
        return 1

if __name__ == "__main__":
    exit(main())