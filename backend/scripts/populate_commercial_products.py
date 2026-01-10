#!/usr/bin/env python3
"""
Script to populate sample commercial products for AssetFlow MVP
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# ruff: noqa: E402
from app.models.commercial import CommercialProduct


async def populate_commercial_products():
    """Populate sample commercial products"""

    sample_products = [
        # Insurance Products
        CommercialProduct(
            category="insurance",
            name="平安人寿重疾险",
            description="覆盖120种重大疾病，保额最高500万，适合家庭保障需求",
            provider="平安保险",
            contact_info={
                "phone": "400-800-0000",
                "name": "张经理",
                "wechat": "pingan_zhang",
                "email": "zhang@pingan.com",
            },
            priority=85,
            target_tags=["family_married_with_kids", "age_30-40", "medium_income"],
            is_active=True,
        ),
        CommercialProduct(
            category="insurance",
            name="太平洋意外险",
            description="全年意外保障，保额100万，适合年轻人群",
            provider="太平洋保险",
            contact_info={
                "phone": "400-900-0000",
                "name": "李顾问",
                "wechat": "taiping_li",
                "email": "li@cpic.com",
            },
            priority=75,
            target_tags=["age_20-30", "risk_aggressive", "low_income"],
            is_active=True,
        ),
        # Broker/Investment Services
        CommercialProduct(
            category="broker",
            name="华泰证券资产配置服务",
            description="专业投资顾问团队，提供个性化资产配置方案，降低投资风险",
            provider="华泰证券",
            contact_info={
                "phone": "400-888-8888",
                "name": "王投顾",
                "wechat": "huatai_wang",
                "email": "wang@htsc.com",
            },
            priority=90,
            target_tags=["high_income", "risk_moderate", "age_40-50"],
            is_active=True,
        ),
        CommercialProduct(
            category="broker",
            name="招商银行私人银行",
            description="高净值客户专属服务，提供房产投资、股权投资等多元化配置建议",
            provider="招商银行",
            contact_info={
                "phone": "400-820-5555",
                "name": "陈理财师",
                "wechat": "cmb_chen",
                "email": "chen@cmbchina.com",
            },
            priority=95,
            target_tags=["high_income", "family_married", "age_40-50"],
            is_active=True,
        ),
        # Investment Products
        CommercialProduct(
            category="investment",
            name="天弘基金货币基金",
            description="低风险理财产品，年化收益2-3%，适合现金管理和流动性储备",
            provider="天弘基金",
            contact_info={
                "phone": "400-700-9999",
                "name": "刘基金经理",
                "wechat": "tianhong_liu",
                "email": "liu@thfund.com",
            },
            priority=70,
            target_tags=["risk_conservative", "low_income", "age_20-30"],
            is_active=True,
        ),
        CommercialProduct(
            category="investment",
            name="易方达混合基金",
            description="中等风险投资产品，历史年化收益8-12%，适合长期投资",
            provider="易方达基金",
            contact_info={
                "phone": "400-881-8088",
                "name": "赵基金顾问",
                "wechat": "efunds_zhao",
                "email": "zhao@efunds.com",
            },
            priority=80,
            target_tags=["risk_moderate", "medium_income", "age_30-40"],
            is_active=True,
        ),
        # Loan Services
        CommercialProduct(
            category="loan",
            name="建设银行个人信用贷",
            description="无抵押信用贷款，利率3.8%-6.5%，快速审批，适合短期资金需求",
            provider="建设银行",
            contact_info={
                "phone": "400-820-0588",
                "name": "孙信贷经理",
                "wechat": "ccb_sun",
                "email": "sun@ccb.com",
            },
            priority=65,
            target_tags=["medium_income", "age_30-40", "family_married"],
            is_active=True,
        ),
        # Consulting Services
        CommercialProduct(
            category="consulting",
            name="德勤财富管理咨询",
            description="专业财富管理咨询服务，制定个性化理财规划和税务优化方案",
            provider="德勤咨询",
            contact_info={
                "phone": "400-820-8888",
                "name": "马咨询师",
                "wechat": "deloitte_ma",
                "email": "ma@deloitte.com",
            },
            priority=88,
            target_tags=["high_income", "risk_moderate", "family_married_with_kids"],
            is_active=True,
        ),
    ]

    try:
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # Check if products already exist
            from sqlmodel import select

            result = await session.execute(select(CommercialProduct))
            existing_products = result.scalars().all()

            if existing_products:
                print(
                    f"Found {len(existing_products)} existing commercial products. Skipping population."
                )
                return

            # Add all sample products
            for product in sample_products:
                session.add(product)

            await session.commit()
            print(f"Successfully populated {len(sample_products)} commercial products!")

            # Print summary
            for product in sample_products:
                print(f"- {product.category}: {product.name} ({product.provider})")

    except Exception as e:
        print(f"Error populating commercial products: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(populate_commercial_products())
