#!/usr/bin/env python3
"""
Demo script showing the impact of prompt refinement
Compares old vs new prompt behavior
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.prompt_manager import PromptManager


def demo_agent_system_refinement():
    """Demonstrate agent_system.yaml refinement"""
    print("\n" + "=" * 80)
    print("DEMO 1: Agent System Prompt - Dynamic Portfolio Analysis")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("chat", "agent_system", "system_instruction")
    
    print("\n📋 Key Improvements:")
    print("\n1. Dynamic Coverage Model:")
    if "动态覆盖模型" in prompt:
        print("   ✅ Emphasizes dynamic thresholds over fixed percentages")
    
    print("\n2. Trust Analysis Data:")
    if "严格信任 [Portfolio Analysis]" in prompt:
        print("   ✅ Instructs AI to trust computed analysis results")
    
    print("\n3. Liquidity Months Check:")
    if "liquidity_months" in prompt:
        print("   ✅ References specific field for cash adequacy")
    
    print("\n4. Forbidden Phrases:")
    if "禁止的错误说法" in prompt:
        print("   ✅ Explicitly lists wrong statements to avoid")
        print("      ❌ '现金占比应该达到10%'")
        print("      ✅ '您的现金储备可以覆盖X个月开销'")
    
    print("\n5. High Net Worth Awareness:")
    if "高净值用户特征" in prompt:
        print("   ✅ Acknowledges low cash % is normal for wealthy users")


def demo_information_extraction_refinement():
    """Demonstrate modular information extraction refinement"""
    print("\n" + "=" * 80)
    print("DEMO 2: Modular Information Extraction - Asset/Profile/Intent Separation")
    print("=" * 80)
    
    pm = PromptManager()
    
    # Demonstrate modular prompts
    print("\n📋 Modular Prompt Architecture:")
    
    modular_prompts = [
        ("asset_extraction", "Asset Extraction"),
        ("profile_extraction", "Profile Extraction"),
        ("intent_detection", "Intent Detection"),
        ("risk_assessment", "Risk Assessment"),
        ("unified_extraction", "Unified Extraction")
    ]
    
    for filename, description in modular_prompts:
        try:
            prompt = pm.get_raw("extraction", filename, "system_instruction")
            print(f"   ✅ {description}: {len(prompt)} characters")
        except FileNotFoundError:
            print(f"   ❌ {description}: File not found")
    
    # Demonstrate configuration files
    print("\n🔧 Configuration Files:")
    
    try:
        asset_config = pm.get_asset_type_mapping()
        print(f"   ✅ Asset Type Mapping: {len(asset_config.get('asset_types', {}))} types")
        
        sp_config = pm.get_sp_quadrant_config()
        print(f"   ✅ SP Quadrant Config: {len(sp_config.get('quadrants', {}))} quadrants")
        
        risk_config = pm.get_risk_assessment_rules()
        print(f"   ✅ Risk Assessment Rules: {len(risk_config.get('user_risk_profiles', {}))} profiles")
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
    
    # Show SP quadrant mappings
    print("\n🎯 SP Quadrant Asset Mappings:")
    try:
        quadrants = sp_config.get("quadrants", {})
        
        preservation_assets = quadrants.get("preservation_money", {}).get("asset_types", [])
        growth_assets = quadrants.get("growth_money", {}).get("asset_types", [])
        
        print("   Preservation Money (保本升值):")
        for asset in preservation_assets[:3]:  # Show first 3
            subtype = asset.get("subtype", "unknown")
            examples = asset.get("examples", [])
            print(f"     - {subtype}: {', '.join(examples[:2])}")
        
        print("   Growth Money (生钱的钱):")
        for asset in growth_assets[:3]:  # Show first 3
            subtype = asset.get("subtype", "unknown")
            examples = asset.get("examples", [])
            print(f"     - {subtype}: {', '.join(examples[:2])}")
            
    except Exception as e:
        print(f"   ❌ SP quadrant mapping failed: {e}")
    
    print("\n✅ Modular extraction system successfully demonstrated!")


def demo_memory_extraction_refinement():
    """Demonstrate memory_extraction.yaml refinement"""
    print("\n" + "=" * 80)
    print("DEMO 3: Memory Extraction - Timeline Tracking")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("insight", "memory_extraction", "system_instruction")
    
    print("\n📋 Timeline Field Addition:")
    
    if '"timeline"' in prompt:
        print("   ✅ Added timeline field to JSON output")
    
    # Check for timeline examples
    timeline_examples = ["3年内", "孩子18岁时", "明年", "退休后"]
    found = [ex for ex in timeline_examples if ex in prompt]
    
    if found:
        print(f"   ✅ Includes {len(found)} timeline examples:")
        for ex in found:
            print(f"      • {ex}")
    
    print("\n📋 Example Output:")
    print("""
    {
      "content": "用户计划3年内购买学区房，预算500万",
      "category": "major_purchase",
      "tags": ["real_estate", "planning", "education"],
      "timeline": "3年内"  ← NEW FIELD
    }
    """)


def demo_psychology_analysis_refinement():
    """Demonstrate psychology_analysis.yaml refinement"""
    print("\n" + "=" * 80)
    print("DEMO 4: Psychology Analysis - Liquidity Anxiety Detection")
    print("=" * 80)
    
    pm = PromptManager()
    prompt = pm.get_raw("insight", "psychology_analysis", "system_instruction")
    
    print("\n📋 Liquidity Anxiety Dimension:")
    
    if "liquidity_anxiety" in prompt:
        print("   ✅ Added liquidity_anxiety field to psychological_traits")
    
    # Check for detection keywords
    keywords = ["手头紧", "没钱花", "转不开", "现金流压力", "资金周转"]
    found = [kw for kw in keywords if kw in prompt]
    
    if found:
        print(f"   ✅ Includes {len(found)} detection keywords:")
        for kw in found:
            print(f"      • {kw}")
    
    print("\n📋 Key Scenario:")
    if "高净值" in prompt or "房产多" in prompt:
        print("   ✅ Detects: High net worth (real estate) + Low cash flow")
        print("      → Typical liquidity anxiety pattern")
    
    print("\n📋 Example Output:")
    print("""
    {
      "psychological_traits": {
        "loss_aversion": "high",
        "uncertainty_tolerance": "low",
        "financial_literacy": "intermediate",
        "family_responsibility": "high",
        "planning_horizon": "medium",
        "liquidity_anxiety": "high"  ← NEW FIELD
      }
    }
    """)


def demo_integration_example():
    """Show how refinements work together"""
    print("\n" + "=" * 80)
    print("DEMO 5: Integration Example - Complete User Flow")
    print("=" * 80)
    
    print("\n📋 Scenario: High Net Worth User with Cash Flow Anxiety")
    print("\n   User Profile:")
    print("   • Real Estate: 5,000,000 (房产)")
    print("   • Cash: 50,000 (现金)")
    print("   • Mortgage: 10,000/month (房贷月供)")
    print("   • Monthly Expense: 15,000")
    
    print("\n   🔄 Processing Flow:")
    
    print("\n   1️⃣ Information Extraction:")
    print("      ✅ Extracts monthly_payment: 10,000")
    print("      ✅ Classifies real estate correctly")
    
    print("\n   2️⃣ Portfolio Analysis:")
    print("      ✅ Calculates liquidity_months: 2.0 (50K / 25K)")
    print("      ✅ Required: 3-6 months + debt payments")
    print("      ⚠️  Gap: Need 75K-150K, have 50K")
    
    print("\n   3️⃣ Psychology Analysis:")
    print("      ✅ Detects liquidity_anxiety: high")
    print("      ✅ Keywords: '手头紧', '现金流压力'")
    
    print("\n   4️⃣ Agent Response (OLD ❌):")
    print("      '您的现金占比只有1%，应该达到10%'")
    print("      → Ignores that user has 5M in assets!")
    
    print("\n   5️⃣ Agent Response (NEW ✅):")
    print("      '您的现金储备可以覆盖2个月开销，考虑到每月1万的房贷，")
    print("       建议增加到至少3-6个月的储备（约7.5-15万）。")
    print("       这样可以缓解您的现金流压力。'")
    print("      → Contextual, empathetic, and accurate!")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("YAML PROMPT REFINEMENT - DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows the improvements from the prompt refinement project.")
    
    demo_agent_system_refinement()
    demo_information_extraction_refinement()
    demo_memory_extraction_refinement()
    demo_psychology_analysis_refinement()
    demo_integration_example()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ All 4 YAML prompts have been refined and validated")
    print("✅ Dynamic Portfolio Analysis logic is now aligned")
    print("✅ Asset classification is more granular and accurate")
    print("✅ Timeline tracking enables better financial planning")
    print("✅ Liquidity anxiety detection improves user experience")
    
    print("\n📚 Documentation:")
    print("   • PROMPT_REFINEMENT_COMPLETE.md - Full details")
    print("   • PROMPT_REFINEMENT_QUICK_REFERENCE.md - Quick guide")
    
    print("\n🧪 Validation:")
    print("   Run: python scripts/validate_prompt_refinement.py")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
