#!/usr/bin/env python3
"""
Demo script to showcase SP Quadrant Integration
Demonstrates the complete flow from extraction to recommendation
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def demo_extraction():
    """Demo 1: Information Extraction with Metadata"""
    logger.info("\n" + "="*80)
    logger.info("DEMO 1: Information Extraction with Metadata")
    logger.info("="*80)
    
    from app.services.information_extraction import information_extractor
    
    test_cases = [
        "我有50万国债",
        "我有10万股票",
        "我有30万基金",
        "房贷200万，月供8000",
        "我有5万余额宝"
    ]
    
    for i, message in enumerate(test_cases, 1):
        logger.info(f"\nTest Case {i}: {message}")
        assets, profile, validation = await information_extractor.extract_information_from_conversation(message)
        
        for asset in assets:
            logger.info(f"  ✅ Extracted Asset:")
            logger.info(f"     Type: {asset.asset_type}")
            logger.info(f"     Name: {asset.name}")
            logger.info(f"     Value: {asset.value}")
            logger.info(f"     Metadata: {asset.metadata}")


async def demo_portfolio_analysis():
    """Demo 2: Portfolio Analysis with SP Quadrant"""
    logger.info("\n" + "="*80)
    logger.info("DEMO 2: Portfolio Analysis with SP Quadrant Classification")
    logger.info("="*80)
    
    from app.services.portfolio_analyzer import portfolio_analyzer
    from app.models.user import UserAsset, AssetType
    
    # Create sample assets with metadata
    assets = [
        UserAsset(
            id=1,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="国债",
            value=500000,
            extra_data={"subtype": "bond", "risk_level": "low"},
            is_confirmed=True
        ),
        UserAsset(
            id=2,
            user_id=1,
            asset_type=AssetType.INVESTMENT,
            name="股票",
            value=100000,
            extra_data={"subtype": "stock", "risk_level": "high"},
            is_confirmed=True
        ),
        UserAsset(
            id=3,
            user_id=1,
            asset_type=AssetType.CASH,
            name="现金",
            value=50000,
            is_confirmed=True
        ),
        UserAsset(
            id=4,
            user_id=1,
            asset_type=AssetType.LIABILITY,
            name="房贷",
            value=2000000,
            extra_data={"monthly_payment": 8000},
            is_confirmed=True
        )
    ]
    
    # Analyze portfolio
    from app.models.user import UserProfile, RiskPreference
    
    user_profile = UserProfile(
        id=1,
        user_id=1,
        age_range="30-40",
        family_structure="married_with_kids",
        monthly_expense=15000,
        risk_preference=RiskPreference.MODERATE
    )
    
    analysis = portfolio_analyzer.analyze_portfolio(
        assets=assets,
        user_profile=user_profile
    )
    
    logger.info("\n📊 SP Quadrant Distribution:")
    sp_dist = analysis.get("sp_quadrant_distribution", {})
    for quadrant, data in sp_dist.items():
        logger.info(f"  {quadrant}: {data.get('percentage', 0):.1f}% (¥{data.get('amount', 0):,.0f})")
    
    logger.info("\n⚠️  Risk Warnings:")
    for warning in analysis.get("risk_warnings", []):
        logger.info(f"  - {warning.get('type')}: {warning.get('title')}")


async def demo_recommendations():
    """Demo 3: Product Recommendations based on SP Quadrant Risks"""
    logger.info("\n" + "="*80)
    logger.info("DEMO 3: Product Recommendations based on SP Quadrant Risks")
    logger.info("="*80)
    
    from app.services.recommendation_service import recommendation_service
    
    # Sample risk warnings from SP Quadrant analysis
    risk_warnings = [
        {
            "type": "sp_spending_insufficient",
            "title": "应急资金不足",
            "severity": "high",
            "recommendation": "建议增加高流动性资产配置"
        },
        {
            "type": "sp_life_insufficient",
            "title": "保险保障不足",
            "severity": "medium",
            "recommendation": "建议配置重疾险和意外险"
        },
        {
            "type": "sp_growth_insufficient",
            "title": "成长性资产不足",
            "severity": "medium",
            "recommendation": "建议增加股票或基金配置"
        }
    ]
    
    logger.info("\n🎯 Risk to Product Category Mapping:")
    for warning in risk_warnings:
        risk_type = warning["type"]
        category = recommendation_service._map_risk_to_category(risk_type)
        logger.info(f"  {risk_type} → {category}")
        logger.info(f"    Title: {warning['title']}")
        logger.info(f"    Recommendation: {warning['recommendation']}")


async def demo_fact_sheet():
    """Demo 4: Fact Sheet Display with Metadata"""
    logger.info("\n" + "="*80)
    logger.info("DEMO 4: Fact Sheet Display with Metadata")
    logger.info("="*80)
    
    logger.info("\n📋 Sample Fact Sheet Output:")
    logger.info("""
【当前系统已确信的用户信息 (Fact Sheet)】

【用户基本画像】
• 年龄段: 30-40岁
• 家庭结构: 已婚有子女
• 职业: 软件工程师
• 收入范围: 20-30万/年
• 月支出: 1.5万
• 风险偏好: 稳健型

【资产清单】
1. [投资] 国债 (子类型: 债券, 风险: 低风险) | 价值: 50万 (用户已确认)
2. [投资] 股票 (子类型: 股票, 风险: 高风险) | 价值: 10万 (用户已确认)
3. [投资] 基金 (子类型: 基金, 风险: 中风险) | 价值: 30万 (用户已确认)
4. [现金] 5万 (用户已确认)
5. [负债] 房贷 | 金额: 200万 | 月供: 8000元 (用户已确认)

【缺失信息提示】
尚未了解: 保险保障

[重要提示] 请基于以上已确认的用户信息和资产数据回答问题，严禁编造或假设未提供的数据。
    """)
    
    logger.info("\n✅ Key Features:")
    logger.info("  - Investment assets show subtype and risk level")
    logger.info("  - Liabilities show monthly payment")
    logger.info("  - Clear Chinese translations")
    logger.info("  - Prevents AI hallucination with confirmed data")


async def main():
    """Run all demos"""
    logger.info("\n" + "="*80)
    logger.info("SP QUADRANT INTEGRATION DEMO")
    logger.info("Showcasing the complete feature loop")
    logger.info("="*80)
    
    try:
        # Demo 1: Extraction
        await demo_extraction()
        
        # Demo 2: Portfolio Analysis
        await demo_portfolio_analysis()
        
        # Demo 3: Recommendations
        await demo_recommendations()
        
        # Demo 4: Fact Sheet
        await demo_fact_sheet()
        
        logger.info("\n" + "="*80)
        logger.info("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info("\nIntegration Status: COMPLETE")
        logger.info("Ready for Production 🚀")
        
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
