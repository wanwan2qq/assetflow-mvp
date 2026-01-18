#!/usr/bin/env python3
"""
Test script for modular information extraction system
Validates the high and medium priority refactoring
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_prompt_manager_config_loading():
    """Test that PromptManager can load configuration files"""
    print("=" * 80)
    print("🔧 TESTING PROMPT MANAGER CONFIG LOADING")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        # Test asset type mapping config
        print("\n✓ Loading asset type mapping...")
        asset_config = prompt_manager.get_asset_type_mapping()
        assert "asset_types" in asset_config, "Missing asset_types"
        assert "real_estate" in asset_config["asset_types"], "Missing real_estate"
        assert "investment" in asset_config["asset_types"], "Missing investment"
        print(f"  Asset types: {list(asset_config['asset_types'].keys())}")
        
        # Test SP quadrant config
        print("\n✓ Loading SP quadrant config...")
        sp_config = prompt_manager.get_sp_quadrant_config()
        assert "quadrants" in sp_config, "Missing quadrants"
        assert "preservation_money" in sp_config["quadrants"], "Missing preservation_money"
        assert "growth_money" in sp_config["quadrants"], "Missing growth_money"
        print(f"  Quadrants: {list(sp_config['quadrants'].keys())}")
        
        # Test risk assessment rules
        print("\n✓ Loading risk assessment rules...")
        risk_config = prompt_manager.get_risk_assessment_rules()
        assert "user_risk_profiles" in risk_config, "Missing user_risk_profiles"
        assert "conservative" in risk_config["user_risk_profiles"], "Missing conservative"
        assert "aggressive" in risk_config["user_risk_profiles"], "Missing aggressive"
        print(f"  Risk profiles: {list(risk_config['user_risk_profiles'].keys())}")
        
        print("\n✅ Configuration loading: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration loading failed: {e}")
        return False

def test_modular_prompt_loading():
    """Test that modular prompts can be loaded"""
    print("\n" + "=" * 80)
    print("📝 TESTING MODULAR PROMPT LOADING")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        # Test modular prompt files
        prompt_files = [
            ("asset_extraction", "Asset Extraction"),
            ("profile_extraction", "Profile Extraction"), 
            ("intent_detection", "Intent Detection"),
            ("risk_assessment", "Risk Assessment"),
            ("unified_extraction", "Unified Extraction")
        ]
        
        for filename, description in prompt_files:
            print(f"\n✓ Loading {description} prompt...")
            try:
                system_prompt = prompt_manager.get_raw(
                    category="extraction",
                    filename=filename,
                    key="system_instruction"
                )
                assert len(system_prompt) > 100, f"{description} prompt too short"
                print(f"  Length: {len(system_prompt)} characters")
                
                # Test user instruction rendering
                user_prompt = prompt_manager.render(
                    category="extraction",
                    filename=filename,
                    key="user_instruction",
                    context_str="user: 我有一套房子",
                    user_message="价值500万",
                    user_profile="{}",
                    current_assets="[]"
                )
                print(f"  Template rendering: ✓")
                
            except FileNotFoundError:
                print(f"  ❌ {description} prompt file not found")
                return False
            except Exception as e:
                print(f"  ❌ Error loading {description}: {e}")
                return False
        
        print("\n✅ Modular prompt loading: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Modular prompt loading failed: {e}")
        return False

def test_sp_quadrant_classification():
    """Test SP quadrant classification logic"""
    print("\n" + "=" * 80)
    print("🎯 TESTING SP QUADRANT CLASSIFICATION")
    print("=" * 80)
    
    try:
        from app.core.prompt_manager import prompt_manager
        
        sp_config = prompt_manager.get_sp_quadrant_config()
        quadrants = sp_config.get("quadrants", {})
        
        # Test preservation money assets
        preservation_assets = quadrants.get("preservation_money", {}).get("asset_types", [])
        preservation_subtypes = [asset.get("subtype") for asset in preservation_assets]
        
        print(f"\n✓ Preservation Money assets:")
        for asset in preservation_assets:
            subtype = asset.get("subtype")
            risk_level = asset.get("risk_level")
            examples = asset.get("examples", [])
            print(f"  {subtype} ({risk_level}): {', '.join(examples[:2])}")
        
        # Test growth money assets
        growth_assets = quadrants.get("growth_money", {}).get("asset_types", [])
        growth_subtypes = [asset.get("subtype") for asset in growth_assets]
        
        print(f"\n✓ Growth Money assets:")
        for asset in growth_assets:
            subtype = asset.get("subtype")
            risk_level = asset.get("risk_level")
            examples = asset.get("examples", [])
            print(f"  {subtype} ({risk_level}): {', '.join(examples[:2])}")
        
        # Verify key mappings
        assert "money_fund" in preservation_subtypes, "Missing money_fund in preservation"
        assert "stock" in growth_subtypes, "Missing stock in growth"
        
        print("\n✅ SP quadrant classification: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ SP quadrant classification failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 MODULAR INFORMATION EXTRACTION SYSTEM TEST")
    print("Testing high and medium priority refactoring results")
    
    tests = [
        test_prompt_manager_config_loading,
        test_modular_prompt_loading,
        test_sp_quadrant_classification,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Modular refactoring successful!")
        return 0
    else:
        print("❌ Some tests failed - Check the output above")
        return 1

if __name__ == "__main__":
    exit(main())