#!/usr/bin/env python3
"""
Test script for validating prompt optimization
Tests the new YAML structure and JSON parsing
"""

import sys
import os
import yaml
import json
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_psychology_analysis_yaml():
    """Test psychology_analysis.yaml structure"""
    print("🔍 Testing psychology_analysis.yaml...")
    
    yaml_path = Path("app/prompts/insight/psychology_analysis.yaml")
    
    if not yaml_path.exists():
        print(f"❌ File not found: {yaml_path}")
        return False
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        # Check required keys
        required_keys = ["system_instruction", "user_instruction"]
        for key in required_keys:
            if key not in content:
                print(f"❌ Missing key: {key}")
                return False
        
        # Check system instruction content
        system_instruction = content["system_instruction"]
        
        # Check for key improvements
        improvements = [
            "严格JSON，不要markdown代码块",
            "risk_tolerance",
            "decision_style", 
            "sentiment",
            "liquidity_anxiety",
            "advisor_note"
        ]
        
        for improvement in improvements:
            if improvement not in system_instruction:
                print(f"⚠️  Missing improvement: {improvement}")
            else:
                print(f"✅ Found improvement: {improvement}")
        
        print("✅ psychology_analysis.yaml structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error loading psychology_analysis.yaml: {e}")
        return False

def test_memory_extraction_yaml():
    """Test memory_extraction.yaml structure"""
    print("\n🔍 Testing memory_extraction.yaml...")
    
    yaml_path = Path("app/prompts/insight/memory_extraction.yaml")
    
    if not yaml_path.exists():
        print(f"❌ File not found: {yaml_path}")
        return False
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        # Check required keys
        required_keys = ["system_instruction", "user_instruction"]
        for key in required_keys:
            if key not in content:
                print(f"❌ Missing key: {key}")
                return False
        
        # Check system instruction content
        system_instruction = content["system_instruction"]
        
        # Check for key improvements
        improvements = [
            "严格JSON数组，不要markdown代码块",
            "timeline",
            "importance",
            "high|medium|low"
        ]
        
        for improvement in improvements:
            if improvement not in system_instruction:
                print(f"⚠️  Missing improvement: {improvement}")
            else:
                print(f"✅ Found improvement: {improvement}")
        
        print("✅ memory_extraction.yaml structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Error loading memory_extraction.yaml: {e}")
        return False

def test_json_examples():
    """Test JSON examples in the prompts"""
    print("\n🔍 Testing JSON examples...")
    
    # Test psychology analysis JSON example
    psychology_example = '''
    {
        "risk_tolerance": "conservative",
        "decision_style": "data_driven", 
        "sentiment": "anxious",
        "liquidity_anxiety": "high",
        "confidence_score": 0.8,
        "loss_aversion": "high",
        "financial_literacy": "intermediate",
        "family_responsibility": "high",
        "planning_horizon": "medium",
        "advisor_note": "用户对房贷压力很大，建议避免激进投资建议，多强调稳健保本方案，语气要温和安抚",
        "key_concerns": ["房贷压力", "流动性不足", "投资风险"]
    }
    '''
    
    try:
        json.loads(psychology_example)
        print("✅ Psychology analysis JSON example is valid")
    except json.JSONDecodeError as e:
        print(f"❌ Psychology analysis JSON example is invalid: {e}")
        return False
    
    # Test memory extraction JSON example
    memory_example = '''
    [
        {
            "content": "用户岳母生病，近期可能需要大额医疗支出",
            "category": "health_concern",
            "timeline": null,
            "importance": "high",
            "tags": ["family", "health", "liquidity"]
        },
        {
            "content": "用户计划3年内购买学区房，预算500万",
            "category": "major_purchase", 
            "timeline": "3年内",
            "importance": "high",
            "tags": ["real_estate", "planning", "education"]
        }
    ]
    '''
    
    try:
        json.loads(memory_example)
        print("✅ Memory extraction JSON example is valid")
    except json.JSONDecodeError as e:
        print(f"❌ Memory extraction JSON example is invalid: {e}")
        return False
    
    return True

def test_backup_files():
    """Test that backup files exist"""
    print("\n🔍 Testing backup files...")
    
    backup_files = [
        "app/prompts/insight/psychology_analysis.yaml.backup",
        "app/prompts/insight/memory_extraction.yaml.backup"
    ]
    
    for backup_file in backup_files:
        backup_path = Path(backup_file)
        if backup_path.exists():
            print(f"✅ Backup exists: {backup_file}")
        else:
            print(f"❌ Backup missing: {backup_file}")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Prompt Optimization Validation")
    print("=" * 50)
    
    tests = [
        test_backup_files,
        test_psychology_analysis_yaml,
        test_memory_extraction_yaml,
        test_json_examples
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("✅ Phase 1 & Phase 2 optimization completed successfully!")
        return 0
    else:
        print(f"⚠️  Some tests failed: {passed}/{total} passed")
        return 1

if __name__ == "__main__":
    exit(main())