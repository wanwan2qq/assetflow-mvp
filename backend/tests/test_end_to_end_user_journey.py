"""
End-to-End User Journey Tests
Tests complete user flows from authentication through asset analysis
"""

import asyncio
import logging
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.main import app
from app.models.commercial import CommercialProduct
from app.models.user import User, UserProfile
from app.services.auth import auth_service

logger = logging.getLogger(__name__)


@pytest.fixture
def test_client():
    """Create test client for E2E testing"""
    return TestClient(app)


@pytest.fixture
async def e2e_user_with_profile(db_session: AsyncSession):
    """Create a comprehensive test user for E2E testing"""
    user = User(
        phone="13800138888",
        device_id="e2e-test-device",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create comprehensive user profile
    profile = UserProfile(
        user_id=user.id,
        age_range="35-45",
        family_structure="married_with_kids",
        risk_preference="moderate",
        monthly_expense=20000.0,
    )

    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)

    user.profile = profile
    token = auth_service.create_access_token(user.id)

    return user, token


@pytest.fixture
async def comprehensive_commercial_products(db_session: AsyncSession):
    """Create comprehensive commercial products for E2E testing"""
    products = [
        # Insurance products
        CommercialProduct(
            category="insurance",
            name="平安人寿综合保险",
            description="全面的人身保险保障，包含意外、疾病、身故保障",
            provider="平安保险",
            contact_info={
                "phone": "400-800-8888",
                "website": "www.pingan.com",
                "email": "service@pingan.com",
            },
            priority=95,
            target_tags=["family", "protection", "comprehensive"],
            is_active=True,
        ),
        CommercialProduct(
            category="insurance",
            name="太平洋重疾险",
            description="专业的重大疾病保险，覆盖100种重疾",
            provider="太平洋保险",
            contact_info={"phone": "400-888-8888", "website": "www.cpic.com.cn"},
            priority=90,
            target_tags=["health", "critical_illness"],
            is_active=True,
        ),
        # Investment products
        CommercialProduct(
            category="broker",
            name="招商证券财富管理",
            description="专业的投资理财服务，提供股票、基金、债券等多元化投资",
            provider="招商证券",
            contact_info={"phone": "400-888-8888", "website": "www.cmschina.com"},
            priority=88,
            target_tags=["investment", "wealth_management", "diversification"],
            is_active=True,
        ),
        CommercialProduct(
            category="investment",
            name="华夏基金定投计划",
            description="稳健的基金定投服务，适合长期投资",
            provider="华夏基金",
            contact_info={"phone": "400-818-6666", "website": "www.chinaamc.com"},
            priority=85,
            target_tags=["fund", "regular_investment", "long_term"],
            is_active=True,
        ),
        # Cash management
        CommercialProduct(
            category="investment",
            name="余额宝货币基金",
            description="低风险货币基金产品，随存随取",
            provider="天弘基金",
            contact_info={"phone": "400-766-7766", "website": "www.thfund.com.cn"},
            priority=80,
            target_tags=["cash_management", "low_risk", "liquidity"],
            is_active=True,
        ),
        # Real estate services
        CommercialProduct(
            category="broker",
            name="链家房产投资咨询",
            description="专业的房产投资咨询服务，帮助优化房产配置",
            provider="链家",
            contact_info={"phone": "400-111-1111", "website": "www.lianjia.com"},
            priority=75,
            target_tags=["real_estate", "investment_consulting"],
            is_active=True,
        ),
    ]

    for product in products:
        db_session.add(product)

    await db_session.commit()

    for product in products:
        await db_session.refresh(product)

    return products


class TestCompleteUserJourney:
    """Test complete user journey from onboarding to recommendations"""

    async def test_complete_family_asset_planning_journey(
        self,
        test_client,
        e2e_user_with_profile,
        comprehensive_commercial_products,
        db_session,
    ):
        """Test complete family asset planning journey"""
        user, token = e2e_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # === Phase 1: User Authentication and Profile Setup ===
            logger.info("Phase 1: Authentication and Profile Setup")

            # Verify user profile
            profile_response = test_client.get(
                f"/api/v1/profiles/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert profile_response.status_code == 200
            profile_data = profile_response.json()["data"]
            assert profile_data["age_range"] == "35-45"
            assert profile_data["family_structure"] == "married_with_kids"
            assert profile_data["monthly_expense"] == 20000.0

            # === Phase 2: Asset Discovery and Input ===
            logger.info("Phase 2: Asset Discovery and Input")

            # Create primary residence (high value, typical for family)
            primary_home = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "real_estate",
                    "name": "北京朝阳区主力住宅",
                    "value": 8000000.0,  # 8M RMB
                    "is_confirmed": True,
                    "extra_data": {
                        "area": 150.0,
                        "city": "北京",
                        "district": "朝阳区",
                        "property_type": "primary_residence",
                        "purchase_year": 2018,
                    },
                },
            )
            assert primary_home.status_code == 200

            # Create investment property
            investment_property = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "real_estate",
                    "name": "上海浦东投资公寓",
                    "value": 4500000.0,  # 4.5M RMB
                    "is_confirmed": True,
                    "extra_data": {
                        "area": 80.0,
                        "city": "上海",
                        "district": "浦东新区",
                        "property_type": "investment",
                        "rental_income": 8000.0,
                    },
                },
            )
            assert investment_property.status_code == 200

            # Create cash assets (multiple accounts)
            cash_savings = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "cash",
                    "name": "银行储蓄账户",
                    "value": 800000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "account_type": "savings",
                        "bank": "招商银行",
                        "interest_rate": 0.025,
                    },
                },
            )
            assert cash_savings.status_code == 200

            emergency_fund = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "cash",
                    "name": "应急资金",
                    "value": 200000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "account_type": "emergency_fund",
                        "purpose": "6个月生活费用",
                    },
                },
            )
            assert emergency_fund.status_code == 200

            # Create investment assets
            stock_portfolio = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "investment",
                    "name": "股票投资组合",
                    "value": 600000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "investment_type": "stocks",
                        "broker": "招商证券",
                        "risk_level": "medium",
                    },
                },
            )
            assert stock_portfolio.status_code == 200

            fund_investment = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "investment",
                    "name": "基金定投",
                    "value": 300000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "investment_type": "mutual_funds",
                        "monthly_contribution": 10000.0,
                        "duration_months": 36,
                    },
                },
            )
            assert fund_investment.status_code == 200

            # Create insurance assets
            life_insurance = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "insurance",
                    "name": "人寿保险",
                    "value": 500000.0,  # Coverage amount
                    "is_confirmed": True,
                    "extra_data": {
                        "insurance_type": "life",
                        "annual_premium": 15000.0,
                        "beneficiary": "spouse_and_children",
                    },
                },
            )
            assert life_insurance.status_code == 200

            # Create liabilities
            mortgage_primary = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "liability",
                    "name": "主力住宅房贷",
                    "value": 3000000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "loan_type": "mortgage",
                        "interest_rate": 0.045,
                        "remaining_years": 15,
                        "monthly_payment": 22000.0,
                    },
                },
            )
            assert mortgage_primary.status_code == 200

            mortgage_investment = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "liability",
                    "name": "投资公寓房贷",
                    "value": 2000000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "loan_type": "investment_mortgage",
                        "interest_rate": 0.05,
                        "remaining_years": 20,
                        "monthly_payment": 13000.0,
                    },
                },
            )
            assert mortgage_investment.status_code == 200

            # === Phase 3: Portfolio Analysis ===
            logger.info("Phase 3: Portfolio Analysis")

            # Get comprehensive portfolio health analysis
            health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert health_response.status_code == 200
            health_data = health_response.json()["data"]

            # Verify calculations
            # Total assets: 8M + 4.5M + 0.8M + 0.2M + 0.6M + 0.3M + 0.5M = 14.9M
            # Total liabilities: 3M + 2M = 5M
            # Net worth: 14.9M - 5M = 9.9M
            expected_net_worth = 9900000.0
            assert (
                abs(health_data["net_worth"] - expected_net_worth) < 1000
            )  # Allow small rounding

            # Real estate ratio: (8M + 4.5M) / 9.9M ≈ 126% (over 100% due to leverage)
            assert (
                health_data["real_estate_ratio"] > 1.0
            )  # Over-leveraged in real estate

            # Liquidity ratio: (0.8M + 0.2M) / (20000 * 6) = 1M / 120K ≈ 8.33
            assert health_data["liquidity_ratio"] > 8.0  # Good liquidity

            # Should have risk warnings
            assert len(health_data["risk_warnings"]) > 0
            warning_types = [w["type"] for w in health_data["risk_warnings"]]
            assert "HIGH_RE_CONCENTRATION" in warning_types

            # === Phase 4: Personalized Recommendations ===
            logger.info("Phase 4: Personalized Recommendations")

            recommendations_response = test_client.post(
                f"/api/v1/recommendations/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "portfolio_health": health_data,
                    "user_profile": {
                        "age_range": "35-45",
                        "family_structure": "married_with_kids",
                        "risk_preference": "moderate",
                        "monthly_expense": 20000.0,
                    },
                },
            )
            assert recommendations_response.status_code == 200
            rec_data = recommendations_response.json()["data"]

            # Should get multiple recommendations
            assert len(rec_data) >= 3

            # Should include diversification recommendations
            categories = [rec["category"] for rec in rec_data]
            assert "investment" in categories or "broker" in categories

            # Should prioritize by weight
            priorities = [rec["priority"] for rec in rec_data]
            assert priorities == sorted(priorities, reverse=True)  # Descending order

            # === Phase 5: Chat Integration with AI Analysis ===
            logger.info("Phase 5: Chat Integration with AI Analysis")

            with patch(
                "app.api.api_v1.endpoints.chat.get_chat_agent"
            ) as mock_get_agent:
                mock_agent = MagicMock()

                # Mock comprehensive AI analysis response
                async def mock_comprehensive_analysis(message, user_id, profile):
                    yield "根据您的资产分析，我为您提供以下专业建议：\n\n"
                    yield "## 资产配置分析\n"
                    yield f"您的净资产为 {health_data['net_worth']:,.0f} 元，"
                    yield f"房产占比为 {health_data['real_estate_ratio'] * 100:.1f}%，"
                    yield f"流动性比率为 {health_data['liquidity_ratio']:.1f}。\n\n"
                    yield "<WIDGET:PORTFOLIO_CHART>\n\n"
                    yield "## 主要风险提示\n"
                    yield "1. **房产集中度过高**：房产占比超过100%，建议适当减持或增加其他投资\n"
                    yield "2. **杠杆率较高**：总负债500万，需要关注利率风险\n\n"
                    yield "## 优化建议\n"
                    yield "### 1. 增加股票和基金投资\n"
                    yield '<WIDGET:ACTION_CARD data="{'
                    yield '"type": "investment", '
                    yield '"title": "招商证券财富管理", '
                    yield '"description": "专业的投资理财服务，提供多元化投资"}'
                    yield '">\n\n'
                    yield "### 2. 完善保险保障\n"
                    yield '<WIDGET:ACTION_CARD data="{'
                    yield '"type": "insurance", '
                    yield '"title": "平安人寿综合保险", '
                    yield '"description": "全面的人身保险保障，适合家庭"}'
                    yield '">\n\n'
                    yield "### 3. 优化现金管理\n"
                    yield '<WIDGET:ACTION_CARD data="{'
                    yield '"type": "investment", '
                    yield '"title": "余额宝货币基金", '
                    yield '"description": "提高现金收益率，保持流动性"}'
                    yield '">\n\n'
                    yield "## 标准普尔四象限建议\n"
                    yield "基于您的家庭结构和风险偏好，建议配置比例：\n"
                    yield "- 保障账户（保险）：10-20%\n"
                    yield "- 杠杆账户（房产）：40-50%\n"
                    yield "- 投资账户（股票基金）：30-40%\n"
                    yield "- 流动账户（现金）：10-15%\n\n"
                    yield "您目前的配置需要向更均衡的方向调整。"

                mock_agent.process_message = mock_comprehensive_analysis

                # Mock UI component extraction
                mock_ui_components = [
                    MagicMock(
                        model_dump=lambda: {
                            "type": "PORTFOLIO_CHART",
                            "data": {"chart_type": "pie", "show_percentages": True},
                            "position": 0,
                        }
                    ),
                    MagicMock(
                        model_dump=lambda: {
                            "type": "ACTION_CARD",
                            "data": {
                                "type": "investment",
                                "title": "招商证券财富管理",
                                "description": "专业的投资理财服务，提供多元化投资",
                                "priority": 88,
                                "contact": {"phone": "400-888-8888"},
                            },
                            "position": 1,
                        }
                    ),
                    MagicMock(
                        model_dump=lambda: {
                            "type": "ACTION_CARD",
                            "data": {
                                "type": "insurance",
                                "title": "平安人寿综合保险",
                                "description": "全面的人身保险保障，适合家庭",
                                "priority": 95,
                                "contact": {"phone": "400-800-8888"},
                            },
                            "position": 2,
                        }
                    ),
                    MagicMock(
                        model_dump=lambda: {
                            "type": "ACTION_CARD",
                            "data": {
                                "type": "investment",
                                "title": "余额宝货币基金",
                                "description": "提高现金收益率，保持流动性",
                                "priority": 80,
                            },
                            "position": 3,
                        }
                    ),
                ]
                mock_agent.extract_ui_components.return_value = mock_ui_components
                mock_get_agent.return_value = mock_agent

                # Send comprehensive analysis request
                chat_response = test_client.post(
                    "/api/v1/chat/chat/message",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"message": "请为我提供详细的资产配置分析和优化建议"},
                )

                assert chat_response.status_code == 200
                chat_data = chat_response.json()

                # Verify comprehensive analysis response
                response_text = chat_data["response"]
                assert "资产配置分析" in response_text
                assert "风险提示" in response_text
                assert "优化建议" in response_text
                assert "标准普尔四象限" in response_text
                assert "PORTFOLIO_CHART" in response_text
                assert "ACTION_CARD" in response_text

                # Verify UI components
                ui_components = chat_data["ui_components"]
                assert len(ui_components) == 4

                component_types = [comp["type"] for comp in ui_components]
                assert "PORTFOLIO_CHART" in component_types
                assert component_types.count("ACTION_CARD") == 3

                # Verify action cards have proper data
                action_cards = [
                    comp for comp in ui_components if comp["type"] == "ACTION_CARD"
                ]
                card_titles = [card["data"]["title"] for card in action_cards]
                assert "招商证券财富管理" in card_titles
                assert "平安人寿综合保险" in card_titles
                assert "余额宝货币基金" in card_titles

            # === Phase 6: Asset Updates and Rebalancing ===
            logger.info("Phase 6: Asset Updates and Rebalancing")

            # Simulate user acting on recommendations - add more investments
            new_investment = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "investment",
                    "name": "新增指数基金投资",
                    "value": 500000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "investment_type": "index_funds",
                        "recommended_by": "招商证券财富管理",
                        "action_date": "2024-01-15",
                    },
                },
            )
            assert new_investment.status_code == 200

            # Add additional insurance
            health_insurance = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "insurance",
                    "name": "重疾险补充保障",
                    "value": 1000000.0,  # Coverage amount
                    "is_confirmed": True,
                    "extra_data": {
                        "insurance_type": "critical_illness",
                        "annual_premium": 8000.0,
                        "recommended_by": "平安人寿综合保险",
                    },
                },
            )
            assert health_insurance.status_code == 200

            # Get updated portfolio analysis
            updated_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert updated_health_response.status_code == 200
            updated_health = updated_health_response.json()["data"]

            # Verify improvements
            # Net worth should be higher: 9.9M + 0.5M + 1M = 11.4M
            assert updated_health["net_worth"] > health_data["net_worth"]

            # Real estate ratio should be lower (better diversification)
            # (8M + 4.5M) / 11.4M ≈ 109.6% (still high but improved)
            assert (
                updated_health["real_estate_ratio"] < health_data["real_estate_ratio"]
            )

            # === Phase 7: Performance and Stress Testing ===
            logger.info("Phase 7: Performance and Stress Testing")

            # Test rapid asset updates (simulating market changes)
            start_time = time.time()

            for i in range(10):
                # Update stock portfolio value (market fluctuation)
                update_response = test_client.put(
                    f"/api/v1/assets/{user.id}/{stock_portfolio.json()['data']['id']}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "value": 600000.0 + (i * 10000),  # Gradual increase
                        "extra_data": {
                            "investment_type": "stocks",
                            "broker": "招商证券",
                            "risk_level": "medium",
                            "last_update": f"2024-01-{15 + i:02d}",
                        },
                    },
                )
                assert update_response.status_code == 200

            update_time = time.time() - start_time
            assert update_time < 5.0  # Should complete within 5 seconds

            # Test portfolio health calculation performance
            start_time = time.time()

            for _ in range(5):
                perf_health_response = test_client.get(
                    f"/api/v1/assets/{user.id}/portfolio/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert perf_health_response.status_code == 200

            calc_time = time.time() - start_time
            assert calc_time < 2.0  # Should complete within 2 seconds

            # === Phase 8: Final Verification ===
            logger.info("Phase 8: Final Verification")

            # Get final asset list
            final_assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert final_assets_response.status_code == 200
            final_assets = final_assets_response.json()["data"]

            # Should have all created assets
            assert len(final_assets) == 11  # 9 original + 2 new

            # Verify asset types distribution
            asset_types = [asset["asset_type"] for asset in final_assets]
            assert asset_types.count("real_estate") == 2
            assert asset_types.count("cash") == 2
            assert asset_types.count("investment") == 3  # 2 original + 1 new
            assert asset_types.count("insurance") == 2  # 1 original + 1 new
            assert asset_types.count("liability") == 2

            # Get final recommendations
            final_rec_response = test_client.post(
                f"/api/v1/recommendations/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "portfolio_health": updated_health,
                    "user_profile": {
                        "age_range": "35-45",
                        "family_structure": "married_with_kids",
                        "risk_preference": "moderate",
                        "monthly_expense": 20000.0,
                    },
                },
            )
            assert final_rec_response.status_code == 200
            final_recs = final_rec_response.json()["data"]

            # Recommendations should be updated based on new portfolio
            assert len(final_recs) >= 2

            logger.info("✅ Complete family asset planning journey test passed!")

        finally:
            app.dependency_overrides.clear()

    async def test_system_stability_under_load(
        self, test_client, e2e_user_with_profile, db_session
    ):
        """Test system stability under concurrent load"""
        user, token = e2e_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Create multiple assets concurrently
            async def create_asset_batch(batch_id: int):
                assets_created = []
                for i in range(5):
                    response = test_client.post(
                        f"/api/v1/assets/{user.id}",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "asset_type": "investment",
                            "name": f"批次{batch_id}_资产{i + 1}",
                            "value": 100000.0 + (batch_id * 1000) + (i * 100),
                            "is_confirmed": True,
                            "extra_data": {"batch_id": batch_id, "asset_index": i},
                        },
                    )
                    if response.status_code == 200:
                        assets_created.append(response.json()["data"]["id"])
                return assets_created

            # Run concurrent asset creation
            start_time = time.time()

            tasks = [create_asset_batch(i) for i in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            creation_time = time.time() - start_time

            # Verify all batches succeeded
            total_created = 0
            for result in results:
                if isinstance(result, list):
                    total_created += len(result)
                else:
                    logger.error(f"Batch creation failed: {result}")

            assert total_created == 15  # 3 batches * 5 assets each
            assert creation_time < 10.0  # Should complete within 10 seconds

            # Test concurrent portfolio health calculations
            start_time = time.time()

            async def get_portfolio_health():
                response = test_client.get(
                    f"/api/v1/assets/{user.id}/portfolio/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
                return response.status_code == 200

            health_tasks = [get_portfolio_health() for _ in range(10)]
            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)

            health_time = time.time() - start_time

            # All health calculations should succeed
            successful_health_calls = sum(
                1 for result in health_results if result is True
            )
            assert successful_health_calls == 10
            assert health_time < 5.0  # Should complete within 5 seconds

            logger.info("✅ System stability under load test passed!")

        finally:
            app.dependency_overrides.clear()


class TestSystemPerformanceMetrics:
    """Test system performance metrics and benchmarks"""

    async def test_api_response_time_benchmarks(
        self, test_client, e2e_user_with_profile, db_session
    ):
        """Test API response time benchmarks"""
        user, token = e2e_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Create baseline assets
            for i in range(20):
                test_client.post(
                    f"/api/v1/assets/{user.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "asset_type": "investment",
                        "name": f"基准资产{i + 1}",
                        "value": 50000.0 * (i + 1),
                        "is_confirmed": True,
                    },
                )

            # Benchmark key endpoints
            endpoints_to_benchmark = [
                ("GET", f"/api/v1/assets/{user.id}", "Asset List"),
                (
                    "GET",
                    f"/api/v1/assets/{user.id}/portfolio/health",
                    "Portfolio Health",
                ),
                ("GET", f"/api/v1/profiles/{user.id}", "User Profile"),
            ]

            benchmark_results = {}

            for method, endpoint, name in endpoints_to_benchmark:
                times = []

                # Run each endpoint 10 times
                for _ in range(10):
                    start_time = time.time()

                    if method == "GET":
                        response = test_client.get(
                            endpoint, headers={"Authorization": f"Bearer {token}"}
                        )

                    end_time = time.time()
                    response_time = end_time - start_time

                    assert response.status_code == 200
                    times.append(response_time)

                # Calculate statistics
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)

                benchmark_results[name] = {
                    "average": avg_time,
                    "maximum": max_time,
                    "minimum": min_time,
                    "samples": len(times),
                }

                # Performance assertions
                assert avg_time < 1.0, (
                    f"{name} average response time {avg_time:.3f}s exceeds 1s"
                )
                assert max_time < 2.0, (
                    f"{name} maximum response time {max_time:.3f}s exceeds 2s"
                )

                logger.info(
                    f"{name}: avg={avg_time:.3f}s, max={max_time:.3f}s, min={min_time:.3f}s"
                )

            # Overall system performance should be good
            overall_avg = sum(
                result["average"] for result in benchmark_results.values()
            ) / len(benchmark_results)
            assert overall_avg < 0.5, (
                f"Overall average response time {overall_avg:.3f}s exceeds 0.5s"
            )

            logger.info("✅ API response time benchmarks passed!")

        finally:
            app.dependency_overrides.clear()

    async def test_data_consistency_under_concurrent_updates(
        self, test_client, e2e_user_with_profile, db_session
    ):
        """Test data consistency under concurrent updates"""
        user, token = e2e_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Create initial asset
            initial_asset = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "investment",
                    "name": "并发测试资产",
                    "value": 1000000.0,
                    "is_confirmed": True,
                },
            )
            assert initial_asset.status_code == 200
            asset_id = initial_asset.json()["data"]["id"]

            # Concurrent update function
            async def update_asset_value(update_id: int, new_value: float):
                try:
                    response = test_client.put(
                        f"/api/v1/assets/{user.id}/{asset_id}",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "value": new_value,
                            "extra_data": {
                                "update_id": update_id,
                                "timestamp": time.time(),
                            },
                        },
                    )
                    return response.status_code == 200, new_value
                except Exception as e:
                    logger.error(f"Update {update_id} failed: {e}")
                    return False, new_value

            # Run concurrent updates
            update_values = [1000000.0 + (i * 10000) for i in range(10)]
            update_tasks = [
                update_asset_value(i, value) for i, value in enumerate(update_values)
            ]

            results = await asyncio.gather(*update_tasks, return_exceptions=True)

            # Count successful updates
            successful_updates = sum(
                1 for result in results if isinstance(result, tuple) and result[0]
            )
            assert successful_updates >= 8, (
                f"Only {successful_updates}/10 updates succeeded"
            )

            # Verify final asset state is consistent
            final_asset_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert final_asset_response.status_code == 200

            assets = final_asset_response.json()["data"]
            test_asset = next(asset for asset in assets if asset["id"] == asset_id)

            # Asset should have one of the update values
            assert test_asset["value"] in update_values

            # Portfolio health should be calculable
            health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert health_response.status_code == 200

            logger.info("✅ Data consistency under concurrent updates test passed!")

        finally:
            app.dependency_overrides.clear()
