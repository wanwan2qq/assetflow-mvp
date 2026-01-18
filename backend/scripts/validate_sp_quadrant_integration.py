#!/usr/bin/env python3
"""
Validation script for Standard & Poor's 4-Quadrant Integration

Tests the complete flow from extraction to recommendation:
1. Extraction: subtype, risk_level, monthly_payment
2. Storage: metadata in UserAsset
3. Fact Sheet: display metadata
4. Portfolio Analysis: SP Quadrant classification
5. Recommendation: SP risk type mapping
"""

import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_extraction():
    """Test extraction of subtype, risk_level, and monthly_payment"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Extraction Layer")
    logger.info("=" * 80)
    
    from app.services.information_extraction import information_extractor
    
    test_cases = [
        {
            "input": "我有 50 万国债",
            "expected": {
                "type": "investment",
                "subtype": "bond",
                "risk_level": "low",
                "value": 500000
            }
        },
        {
            "input": "我有 10 万股票",
            "expected": {
                "type": "investment",
                "subtype": "stock",
                "risk_level": "high",
                "value": 100000
            }
        },
        {
            "input": "我有 30 万基金",
            "expected": {
                "type": "investment",
                "subtype": "fund",
                "risk_level": "medium",
                "value": 300000
            }
        },
        {
            "input": "房贷 200 万，月供 8000",
            "expected": {
                "type": "liability",
                "value": 2000000,
                "monthly_payment": 8000
            }
        },
        {
            "input": "车贷月供 3000",
            "expected": {
                "type": "liability",
                "monthly_payment": 3000
            }
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {test_case['input']}")
        
        try:
            assets, profile, validation = await information_extractor.extract_information_from_conversation(
                test_case["input"]
            )
            
            if not assets:
                logger.error(f"  ❌ FAILED: No assets extracted")
                failed += 1
                continue
            
            asset = assets[0]
            expected = test_case["expected"]
            
            # Check asset type
            if asset.asset_type.value != expected["type"]:
                logger.error(f"  ❌ FAILED: Expected type '{expected['type']}', got '{asset.asset_type.value}'")
                failed += 1
                continue
            
            # Check value if expected
            if "value" in expected and asset.value != expected["value"]:
                logger.error(f"  ❌ FAILED: Expected value {expected['value']}, got {asset.value}")
                failed += 1
                continue
            
            # Check metadata
            metadata = asset.metadata or {}
            
            if "subtype" in expected:
                if metadata.get("subtype") != expected["subtype"]:
                    logger.error(f"  ❌ FAILED: Expected subtype '{expected['subtype']}', got '{metadata.get('subtype')}'")
                    failed += 1
                    continue
            
            if "risk_level" in expected:
                if metadata.get("risk_level") != expected["risk_level"]:
                    logger.error(f"  ❌ FAILED: Expected risk_level '{expected['risk_level']}', got '{metadata.get('risk_level')}'")
                    failed += 1
                    continue
            
            if "monthly_payment" in expected:
                if metadata.get("monthly_payment") != expected["monthly_payment"]:
                    logger.error(f"  ❌ FAILED: Expected monthly_payment {expected['monthly_payment']}, got {metadata.get('monthly_payment')}")
                    failed += 1
                    continue
            
            logger.info(f"  ✅ PASSED")
            logger.info(f"     Type: {asset.asset_type.value}")
            logger.info(f"     Value: {asset.value}")
            logger.info(f"     Metadata: {metadata}")
            passed += 1
            
        except Exception as e:
            logger.error(f"  ❌ FAILED: {e}")
            failed += 1
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Extraction Tests: {passed} passed, {failed} failed")
    logger.info(f"{'=' * 80}")
    
    return passed, failed


async def test_fact_sheet_display():
    """Test fact sheet display with metadata"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Fact Sheet Display")
    logger.info("=" * 80)
    
    from app.services.chat_agent import ChatAgent
    from app.models.user import UserAsset, AssetType
    from app.core.database import get_db_session
    from sqlmodel import select
    
    # Create test user with assets
    test_user_id = 99999
    
    async for session in get_db_session():
        # Clean up existing test data
        existing_assets = await session.execute(
            select(UserAsset).where(UserAsset.user_id == test_user_id)
        )
        for asset in existing_assets.scalars().all():
            await session.delete(asset)
        await session.commit()
        
        # Create test assets with metadata
        test_assets = [
            UserAsset(
                user_id=test_user_id,
                asset_type=AssetType.INVESTMENT,
                name="国债",
                value=500000,
                is_confirmed=True,
                extra_data={
                    "subtype": "bond",
                    "risk_level": "low"
                }
            ),
            UserAsset(
                user_id=test_user_id,
                asset_type=AssetType.INVESTMENT,
                name="股票",
                value=100000,
                is_confirmed=True,
                extra_data={
                    "subtype": "stock",
                    "risk_level": "high"
                }
            ),
            UserAsset(
                user_id=test_user_id,
                asset_type=AssetType.LIABILITY,
                name="房贷",
                value=2000000,
                is_confirmed=True,
                extra_data={
                    "monthly_payment": 8000
                }
            )
        ]
        
        for asset in test_assets:
            session.add(asset)
        await session.commit()
        
        logger.info(f"Created {len(test_assets)} test assets for user {test_user_id}")
        break
    
    # Generate fact sheet
    agent = ChatAgent()
    fact_sheet = await agent._generate_fact_sheet(test_user_id)
    
    logger.info("\nGenerated Fact Sheet:")
    logger.info("-" * 80)
    logger.info(fact_sheet)
    logger.info("-" * 80)
    
    # Validate fact sheet content
    checks = [
        ("债券" in fact_sheet, "Investment subtype (债券) displayed"),
        ("低风险" in fact_sheet, "Risk level (低风险) displayed"),
        ("高风险" in fact_sheet, "Risk level (高风险) displayed"),
        ("月供: 8000元" in fact_sheet, "Monthly payment displayed"),
    ]
    
    passed = 0
    failed = 0
    
    for check, description in checks:
        if check:
            logger.info(f"  ✅ {description}")
            passed += 1
        else:
            logger.error(f"  ❌ {description}")
            failed += 1
    
    # Clean up test data
    async for session in get_db_session():
        existing_assets = await session.execute(
            select(UserAsset).where(UserAsset.user_id == test_user_id)
        )
        for asset in existing_assets.scalars().all():
            await session.delete(asset)
        await session.commit()
        break
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Fact Sheet Tests: {passed} passed, {failed} failed")
    logger.info(f"{'=' * 80}")
    
    return passed, failed


async def test_recommendation_mapping():
    """Test recommendation service SP risk type mapping"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Recommendation Service Mapping")
    logger.info("=" * 80)
    
    from app.services.recommendation_service import recommendation_service
    
    test_cases = [
        ("sp_spending_insufficient", "investment", "Spending Money (要花的钱)"),
        ("sp_life_insufficient", "insurance", "Life Money (保命的钱)"),
        ("sp_growth_insufficient", "broker", "Growth Money (生钱的钱)"),
        ("sp_preservation_insufficient", "investment", "Preservation Money (保本升值的钱)"),
    ]
    
    passed = 0
    failed = 0
    
    for risk_type, expected_category, description in test_cases:
        result = recommendation_service._map_risk_to_category(risk_type)
        
        if result == expected_category:
            logger.info(f"  ✅ {description}: {risk_type} → {expected_category}")
            passed += 1
        else:
            logger.error(f"  ❌ {description}: {risk_type} → {result} (expected {expected_category})")
            failed += 1
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Recommendation Tests: {passed} passed, {failed} failed")
    logger.info(f"{'=' * 80}")
    
    return passed, failed


async def test_portfolio_analyzer_integration():
    """Test portfolio analyzer with metadata"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Portfolio Analyzer Integration")
    logger.info("=" * 80)
    
    from app.services.portfolio_analyzer import portfolio_analyzer
    from app.models.user import UserAsset, AssetType
    
    # Create test assets with metadata
    test_assets = [
        UserAsset(
            user_id=99999,
            asset_type=AssetType.INVESTMENT,
            name="国债",
            value=500000,
            is_confirmed=True,
            extra_data={
                "subtype": "bond",
                "risk_level": "low"
            }
        ),
        UserAsset(
            user_id=99999,
            asset_type=AssetType.INVESTMENT,
            name="股票",
            value=100000,
            is_confirmed=True,
            extra_data={
                "subtype": "stock",
                "risk_level": "high"
            }
        ),
        UserAsset(
            user_id=99999,
            asset_type=AssetType.CASH,
            name="现金",
            value=50000,
            is_confirmed=True
        )
    ]
    
    # Analyze portfolio
    analysis = portfolio_analyzer.analyze_portfolio(test_assets, None)
    
    logger.info("\nPortfolio Analysis Result:")
    logger.info("-" * 80)
    logger.info(json.dumps(analysis, indent=2, ensure_ascii=False))
    logger.info("-" * 80)
    
    # Validate analysis
    checks = [
        ("sp_quadrant_distribution" in analysis, "SP Quadrant distribution present"),
        ("risk_warnings" in analysis, "Risk warnings present"),
        (len(analysis.get("risk_warnings", [])) > 0, "Risk warnings generated"),
    ]
    
    passed = 0
    failed = 0
    
    for check, description in checks:
        if check:
            logger.info(f"  ✅ {description}")
            passed += 1
        else:
            logger.error(f"  ❌ {description}")
            failed += 1
    
    # Check if assets are classified correctly
    sp_dist = analysis.get("sp_quadrant_distribution", {})
    if sp_dist:
        logger.info("\nSP Quadrant Distribution:")
        for quadrant, data in sp_dist.items():
            logger.info(f"  {quadrant}: {data.get('percentage', 0):.1f}% ({data.get('amount', 0)/10000:.1f}万)")
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Portfolio Analyzer Tests: {passed} passed, {failed} failed")
    logger.info(f"{'=' * 80}")
    
    return passed, failed


async def main():
    """Run all validation tests"""
    logger.info("\n" + "=" * 80)
    logger.info("STANDARD & POOR'S 4-QUADRANT INTEGRATION VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Extraction
    try:
        passed, failed = await test_extraction()
        total_passed += passed
        total_failed += failed
    except Exception as e:
        logger.error(f"Extraction test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        total_failed += 1
    
    # Test 2: Fact Sheet Display
    try:
        passed, failed = await test_fact_sheet_display()
        total_passed += passed
        total_failed += failed
    except Exception as e:
        logger.error(f"Fact sheet test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        total_failed += 1
    
    # Test 3: Recommendation Mapping
    try:
        passed, failed = await test_recommendation_mapping()
        total_passed += passed
        total_failed += failed
    except Exception as e:
        logger.error(f"Recommendation test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        total_failed += 1
    
    # Test 4: Portfolio Analyzer Integration
    try:
        passed, failed = await test_portfolio_analyzer_integration()
        total_passed += passed
        total_failed += failed
    except Exception as e:
        logger.error(f"Portfolio analyzer test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        total_failed += 1
    
    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Passed: {total_passed}")
    logger.info(f"Total Failed: {total_failed}")
    logger.info(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    logger.info(f"Completed at: {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    if total_failed == 0:
        logger.info("\n🎉 ALL TESTS PASSED! Integration is complete and working correctly.")
    else:
        logger.warning(f"\n⚠️  {total_failed} tests failed. Please review the errors above.")
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
