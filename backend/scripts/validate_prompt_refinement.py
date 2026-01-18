#!/usr/bin/env python3
"""
Validation script for refined YAML prompts
Tests the alignment with Dynamic Portfolio Analysis logic
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.prompt_manager import PromptManager


def test_agent_system_prompt():
    """Test Task 1: Agent system prompt has dynamic logic"""
    print("\n" + "=" * 80)
    print("Task 1: Testing agent_system.yaml - Dynamic Portfolio Analysis Logic")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("chat", "agent_system", "system_instruction")
    
    # Check for key dynamic concepts
    checks = {
        "Dynamic Coverage Model": "动态覆盖模型" in prompt,
        "Liquidity Months Field": "liquidity_months" in prompt,
        "Trust Analysis Data": "严格信任 [Portfolio Analysis]" in prompt,
        "No Fixed Percentages": "不要用固定比例判断" in prompt,
        "Allocation Gaps": "allocation_gaps" in prompt,
        "Forbidden Phrases": "禁止的错误说法" in prompt,
        "High Net Worth Note": "高净值用户特征" in prompt,
    }
    
    print("\n✅ Checks:")
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    # Check that old fixed percentages are removed
    bad_phrases = [
        "死守10%的比例",  # Should be removed or contextualized
        "保费是否达到20%",  # Should be removed
    ]
    
    print("\n🔍 Checking for removed fixed percentage language:")
    for phrase in bad_phrases:
        if phrase in prompt:
            print(f"  ⚠️  WARNING: Found old phrase: '{phrase}'")
        else:
            print(f"  ✅ Good: Removed '{phrase}'")
    
    all_passed = all(checks.values())
    return all_passed


def test_information_extraction_prompt():
    """Test Task 2: Information extraction has modular architecture with granular subtypes"""
    print("\n" + "=" * 80)
    print("Task 2: Testing Modular Information Extraction - Asset/Profile/Intent Separation")
    print("=" * 80)
    
    pm = PromptManager()
    
    # Test asset extraction prompt
    try:
        asset_prompt = pm.get_raw("extraction", "asset_extraction", "system_instruction")
        asset_exists = True
    except FileNotFoundError:
        asset_exists = False
        asset_prompt = ""
    
    # Test profile extraction prompt
    try:
        profile_prompt = pm.get_raw("extraction", "profile_extraction", "system_instruction")
        profile_exists = True
    except FileNotFoundError:
        profile_exists = False
        profile_prompt = ""
    
    # Test intent detection prompt
    try:
        intent_prompt = pm.get_raw("extraction", "intent_detection", "system_instruction")
        intent_exists = True
    except FileNotFoundError:
        intent_exists = False
        intent_prompt = ""
    
    # Check for modular architecture
    checks = {
        "Asset Extraction File Exists": asset_exists,
        "Profile Extraction File Exists": profile_exists,
        "Intent Detection File Exists": intent_exists,
        "Asset Extraction Specialization": asset_exists and "specialized asset extraction" in asset_prompt.lower(),
        "Profile Extraction Specialization": profile_exists and "specialized user profile extraction" in profile_prompt.lower(),
        "Intent Detection Specialization": intent_exists and "specialized intent detection" in intent_prompt.lower(),
    }
    
    print("\n✅ Modular Architecture Checks:")
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    # Test configuration file loading
    try:
        asset_config = pm.get_asset_type_mapping()
        sp_config = pm.get_sp_quadrant_config()
        risk_config = pm.get_risk_assessment_rules()
        
        config_checks = {
            "Asset Type Mapping": "asset_types" in asset_config,
            "SP Quadrant Config": "quadrants" in sp_config,
            "Risk Assessment Rules": "user_risk_profiles" in risk_config,
            "Preservation Money Quadrant": "preservation_money" in sp_config.get("quadrants", {}),
            "Growth Money Quadrant": "growth_money" in sp_config.get("quadrants", {}),
        }
        
        print("\n🔧 Configuration File Checks:")
        for check_name, result in config_checks.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {check_name}")
            
    except Exception as e:
        print(f"\n❌ Configuration loading failed: {e}")
        config_checks = {"Config Loading": False}
    
    # Verify specific subtype mappings in config if available
    if "sp_config" in locals() and sp_config:
        print("\n🔍 Verifying SP quadrant mappings in config:")
        quadrants = sp_config.get("quadrants", {})
        
        preservation_assets = quadrants.get("preservation_money", {}).get("asset_types", [])
        growth_assets = quadrants.get("growth_money", {}).get("asset_types", [])
        
        preservation_subtypes = [asset.get("subtype") for asset in preservation_assets]
        growth_subtypes = [asset.get("subtype") for asset in growth_assets]
        
        if "money_fund" in preservation_subtypes:
            print("  ✅ 货币基金 -> preservation_money (low risk)")
        else:
            print("  ❌ Missing 货币基金 in preservation_money")
        
        if "stock" in growth_subtypes:
            print("  ✅ 股票 -> growth_money (high risk)")
        else:
            print("  ❌ Missing 股票 in growth_money")
    
    all_passed = all(checks.values()) and all(config_checks.values())
    return all_passed


def test_memory_extraction_prompt():
    """Test Task 3: Memory extraction has timeline field"""
    print("\n" + "=" * 80)
    print("Task 3: Testing memory_extraction.yaml - Timeline Extraction")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("insight", "memory_extraction", "system_instruction")
    
    # Check for timeline field
    checks = {
        "Timeline Field in JSON": '"timeline"' in prompt,
        "Timeline Examples": "3年内" in prompt or "孩子18岁时" in prompt,
        "Timeline Instruction": "timeline 字段" in prompt or "时间线" in prompt,
        "Null Timeline Handling": "null" in prompt,
    }
    
    print("\n✅ Checks:")
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    # Check for timeline examples in JSON format
    print("\n🔍 Checking timeline examples:")
    timeline_examples = ["3年内", "孩子18岁时", "明年", "退休后"]
    found_examples = [ex for ex in timeline_examples if ex in prompt]
    
    if found_examples:
        print(f"  ✅ Found timeline examples: {', '.join(found_examples)}")
    else:
        print("  ⚠️  No timeline examples found")
    
    all_passed = all(checks.values())
    return all_passed


def test_psychology_analysis_prompt():
    """Test Task 4: Psychology analysis has liquidity anxiety"""
    print("\n" + "=" * 80)
    print("Task 4: Testing psychology_analysis.yaml - Liquidity Anxiety Dimension")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("insight", "psychology_analysis", "system_instruction")
    
    # Check for liquidity anxiety field
    checks = {
        "Liquidity Anxiety Field": "liquidity_anxiety" in prompt,
        "Liquidity Anxiety Levels": "high|medium|low" in prompt,
        "Liquidity Keywords": "手头紧" in prompt or "现金流压力" in prompt,
        "High Net Worth Scenario": "高净值" in prompt or "房产多" in prompt,
        "Cash Flow Pressure": "cash flow" in prompt or "现金流" in prompt,
    }
    
    print("\n✅ Checks:")
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {check_name}")
    
    # Check for specific keywords
    print("\n🔍 Checking liquidity anxiety keywords:")
    keywords = ["手头紧", "没钱花", "转不开", "现金流压力", "资金周转"]
    found_keywords = [kw for kw in keywords if kw in prompt]
    
    if found_keywords:
        print(f"  ✅ Found keywords: {', '.join(found_keywords)}")
    else:
        print("  ⚠️  No liquidity anxiety keywords found")
    
    # Verify JSON structure includes liquidity_anxiety
    if '"liquidity_anxiety"' in prompt:
        print("  ✅ liquidity_anxiety field in JSON structure")
    else:
        print("  ❌ liquidity_anxiety field NOT in JSON structure")
    
    all_passed = all(checks.values())
    return all_passed


def main():
    """Run all validation tests"""
    print("\n" + "=" * 80)
    print("YAML PROMPT REFINEMENT VALIDATION")
    print("=" * 80)
    
    results = {
        "Task 1 (agent_system.yaml)": test_agent_system_prompt(),
        "Task 2 (information_extraction.yaml)": test_information_extraction_prompt(),
        "Task 3 (memory_extraction.yaml)": test_memory_extraction_prompt(),
        "Task 4 (psychology_analysis.yaml)": test_psychology_analysis_prompt(),
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    for task, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {task}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All validation tests PASSED!")
        print("\n✅ Prompt refinement is complete and aligned with Dynamic Portfolio Analysis")
        return 0
    else:
        print("\n⚠️  Some validation tests FAILED")
        print("Please review the failed checks above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
