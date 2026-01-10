"""
Complete User Flow Integration Tests
Tests the entire AssetFlow user journey from authentication to asset analysis
"""

import asyncio
import logging
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
    """Create test client for integration testing"""
    return TestClient(app)


@pytest.fixture
async def test_user_with_profile(db_session: AsyncSession):
    """Create a test user with profile for complete flow testing"""
    user = User(
        phone="13800138000",
        device_id="test-device-integration",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create user profile
    profile = UserProfile(
        user_id=user.id,
        age_range="30-40",
        family_structure="married_with_kids",
        risk_preference="moderate",
        monthly_expense=15000.0,
    )

    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)

    user.profile = profile
    token = auth_service.create_access_token(user.id)

    return user, token


@pytest.fixture
async def commercial_products(db_session: AsyncSession):
    """Create test commercial products for recommendations"""
    products = [
        CommercialProduct(
            category="insurance",
            name="平安人寿保险",
            description="全面的人身保险保障",
            provider="平安保险",
            contact_info={"phone": "400-800-8888", "website": "www.pingan.com"},
            priority=90,
            target_tags=["family", "protection"],
            is_active=True,
        ),
        CommercialProduct(
            category="broker",
            name="招商证券投资顾问",
            description="专业的投资理财服务",
            provider="招商证券",
            contact_info={"phone": "400-888-8888", "website": "www.cmschina.com"},
            priority=85,
            target_tags=["investment", "wealth_management"],
            is_active=True,
        ),
        CommercialProduct(
            category="investment",
            name="余额宝货币基金",
            description="低风险货币基金产品",
            provider="天弘基金",
            contact_info={"phone": "400-766-7766", "website": "www.thfund.com.cn"},
            priority=80,
            target_tags=["cash_management", "low_risk"],
            is_active=True,
        ),
    ]

    for product in products:
        db_session.add(product)

    await db_session.commit()

    for product in products:
        await db_session.refresh(product)

    return products


class TestCompleteUserFlow:
    """Test complete user flow from authentication to asset analysis"""

    async def test_complete_asset_onboarding_flow(
        self, test_client, test_user_with_profile, commercial_products, db_session
    ):
        """Test complete user flow: login -> chat -> asset creation -> analysis -> recommendations"""
        user, token = test_user_with_profile

        # Override dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Step 1: Verify user authentication
            response = test_client.get(
                f"/api/v1/profiles/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            profile_data = response.json()
            assert profile_data["data"]["age_range"] == "30-40"

            # Step 2: Create initial assets through API (simulating chat extraction)
            # Create real estate asset
            real_estate_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "real_estate",
                    "name": "北京天通苑北一区",
                    "value": 4500000.0,
                    "is_confirmed": True,
                    "extra_data": {
                        "area": 120.0,
                        "city": "北京",
                        "community": "天通苑北一区",
                        "estimated_price_per_sqm": 37500.0,
                    },
                },
            )
            assert real_estate_response.status_code == 200

            # Create cash asset
            cash_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "cash",
                    "name": "银行存款",
                    "value": 500000.0,
                    "is_confirmed": True,
                    "extra_data": {"account_type": "savings"},
                },
            )
            assert cash_response.status_code == 200

            # Create investment asset
            investment_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "investment",
                    "name": "股票投资",
                    "value": 300000.0,
                    "is_confirmed": True,
                    "extra_data": {"investment_type": "stocks"},
                },
            )
            assert investment_response.status_code == 200

            # Create liability
            liability_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "liability",
                    "name": "房贷",
                    "value": 2000000.0,
                    "is_confirmed": True,
                    "extra_data": {"loan_type": "mortgage"},
                },
            )
            assert liability_response.status_code == 200

            # Step 3: Verify assets were created
            assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert assets_response.status_code == 200
            assets_data = assets_response.json()
            assert assets_data["success"] is True
            assert len(assets_data["data"]) == 4

            # Step 4: Get portfolio health analysis
            health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert health_response.status_code == 200
            health_data = health_response.json()

            # Verify portfolio calculations
            assert health_data["success"] is True
            portfolio = health_data["data"]

            # Net worth = 4,500,000 + 500,000 + 300,000 - 2,000,000 = 3,300,000
            assert portfolio["net_worth"] == 3300000.0

            # Real estate ratio = 4,500,000 / 3,300,000 ≈ 1.36 (136%)
            assert portfolio["real_estate_ratio"] > 1.0  # Over 100%

            # Liquidity ratio = 500,000 / (15,000 * 6) = 5.56
            assert portfolio["liquidity_ratio"] > 5.0

            # Should have risk warnings for high real estate concentration
            assert len(portfolio["risk_warnings"]) > 0
            high_re_warning = any(
                warning["type"] == "HIGH_RE_CONCENTRATION"
                for warning in portfolio["risk_warnings"]
            )
            assert high_re_warning

            # Step 5: Get recommendations based on portfolio analysis
            recommendations_response = test_client.post(
                f"/api/v1/recommendations/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "portfolio_health": portfolio,
                    "user_profile": {
                        "age_range": "30-40",
                        "family_structure": "married_with_kids",
                        "risk_preference": "moderate",
                    },
                },
            )
            assert recommendations_response.status_code == 200
            rec_data = recommendations_response.json()

            # Should get recommendations for diversification
            assert rec_data["success"] is True
            recommendations = rec_data["data"]
            assert len(recommendations) > 0

            # Should include investment and insurance recommendations
            categories = [rec["category"] for rec in recommendations]
            assert "investment" in categories or "broker" in categories

            # Step 6: Test chat message processing with complete context
            with patch(
                "app.api.api_v1.endpoints.chat.get_chat_agent"
            ) as mock_get_agent:
                mock_agent = MagicMock()

                # Mock AI response with UI components
                async def mock_process_message(message, user_id, profile):
                    yield "根据您的资产分析，我发现您的房产占比过高（136%），"
                    yield "建议您考虑以下配置调整：\n\n"
                    yield "<WIDGET:PORTFOLIO_CHART>\n\n"
                    yield "1. 增加股票和基金投资，降低房产占比\n"
                    yield '<WIDGET:ACTION_CARD data="{'
                    yield '"type": "investment", '
                    yield '"title": "招商证券投资顾问", '
                    yield '"description": "专业的投资理财服务"}'
                    yield '">\n\n'
                    yield "2. 考虑购买人身保险保障\n"
                    yield '<WIDGET:ACTION_CARD data="{'
                    yield '"type": "insurance", '
                    yield '"title": "平安人寿保险", '
                    yield '"description": "全面的人身保险保障"}'
                    yield '">'

                mock_agent.process_message = mock_process_message

                # Mock UI component extraction
                mock_ui_components = [
                    MagicMock(
                        model_dump=lambda: {
                            "type": "PORTFOLIO_CHART",
                            "data": {"chart_type": "pie"},
                            "position": 0,
                        }
                    ),
                    MagicMock(
                        model_dump=lambda: {
                            "type": "ACTION_CARD",
                            "data": {
                                "type": "investment",
                                "title": "招商证券投资顾问",
                                "description": "专业的投资理财服务",
                            },
                            "position": 1,
                        }
                    ),
                    MagicMock(
                        model_dump=lambda: {
                            "type": "ACTION_CARD",
                            "data": {
                                "type": "insurance",
                                "title": "平安人寿保险",
                                "description": "全面的人身保险保障",
                            },
                            "position": 2,
                        }
                    ),
                ]
                mock_agent.extract_ui_components.return_value = mock_ui_components
                mock_get_agent.return_value = mock_agent

                # Send chat message
                chat_response = test_client.post(
                    "/api/v1/chat/chat/message",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"message": "请分析我的资产配置并给出建议"},
                )

                assert chat_response.status_code == 200
                chat_data = chat_response.json()

                # Verify AI response contains analysis and recommendations
                assert "房产占比过高" in chat_data["response"]
                assert "PORTFOLIO_CHART" in chat_data["response"]
                assert "ACTION_CARD" in chat_data["response"]

                # Verify UI components were extracted
                assert len(chat_data["ui_components"]) == 3
                component_types = [comp["type"] for comp in chat_data["ui_components"]]
                assert "PORTFOLIO_CHART" in component_types
                assert "ACTION_CARD" in component_types

            # Step 7: Test asset update flow
            assets = assets_data["data"]
            real_estate_asset = next(
                asset for asset in assets if asset["asset_type"] == "real_estate"
            )

            update_response = test_client.put(
                f"/api/v1/assets/{user.id}/{real_estate_asset['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "value": 4800000.0,  # Updated valuation
                    "extra_data": {
                        "area": 120.0,
                        "city": "北京",
                        "community": "天通苑北一区",
                        "estimated_price_per_sqm": 40000.0,
                        "valuation_date": "2024-01-15",
                    },
                },
            )
            assert update_response.status_code == 200

            # Verify updated portfolio health
            updated_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert updated_health_response.status_code == 200
            updated_health = updated_health_response.json()["data"]

            # Net worth should be higher now: 4,800,000 + 500,000 + 300,000 - 2,000,000 = 3,600,000
            assert updated_health["net_worth"] == 3600000.0
            assert updated_health["net_worth"] > portfolio["net_worth"]

        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    async def test_error_handling_in_complete_flow(
        self, test_client, test_user_with_profile, db_session
    ):
        """Test error handling throughout the complete user flow"""
        user, token = test_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Test 1: Invalid asset creation
            invalid_asset_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "invalid_type",
                    "name": "Test Asset",
                    "value": -1000.0,  # Negative value
                },
            )
            assert invalid_asset_response.status_code == 422  # Validation error

            # Test 2: Access control - try to access different user's assets
            different_user_id = user.id + 999
            unauthorized_response = test_client.get(
                f"/api/v1/assets/{different_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert unauthorized_response.status_code == 403

            # Test 3: Portfolio health with no assets
            empty_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert empty_health_response.status_code == 200
            empty_health = empty_health_response.json()["data"]
            assert empty_health["net_worth"] == 0.0
            assert empty_health["real_estate_ratio"] == 0.0
            assert empty_health["liquidity_ratio"] == 0.0

            # Test 4: Recommendations with empty portfolio
            empty_rec_response = test_client.post(
                f"/api/v1/recommendations/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "portfolio_health": empty_health,
                    "user_profile": {
                        "age_range": "30-40",
                        "family_structure": "married_with_kids",
                        "risk_preference": "moderate",
                    },
                },
            )
            assert empty_rec_response.status_code == 200
            empty_rec_data = empty_rec_response.json()
            # Should still return some basic recommendations
            assert empty_rec_data["success"] is True

        finally:
            app.dependency_overrides.clear()

    async def test_concurrent_user_flows(self, test_client, db_session):
        """Test that multiple users can use the system concurrently without interference"""
        # Create two test users
        user1 = User(phone="13800138001", device_id="device-1")
        user2 = User(phone="13800138002", device_id="device-2")

        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        token1 = auth_service.create_access_token(user1.id)
        token2 = auth_service.create_access_token(user2.id)

        # Create assets for both users concurrently
        async def create_user_assets(user_id, token, asset_value):
            def override_get_current_user():
                return user1 if user_id == user1.id else user2

            app.dependency_overrides[get_current_user] = override_get_current_user

            try:
                response = test_client.post(
                    f"/api/v1/assets/{user_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "asset_type": "real_estate",
                        "name": f"用户{user_id}的房产",
                        "value": asset_value,
                        "is_confirmed": True,
                    },
                )
                return response
            finally:
                app.dependency_overrides.clear()

        # Create assets concurrently
        responses = await asyncio.gather(
            asyncio.create_task(create_user_assets(user1.id, token1, 3000000.0)),
            asyncio.create_task(create_user_assets(user2.id, token2, 5000000.0)),
            return_exceptions=True,
        )

        # Both should succeed
        for response in responses:
            if isinstance(response, Exception):
                pytest.fail(f"Concurrent operation failed: {response}")
            assert response.status_code == 200

        # Verify data isolation - each user should only see their own assets
        def override_get_current_user_1():
            return user1

        def override_get_current_user_2():
            return user2

        # Check user1's assets
        app.dependency_overrides[get_current_user] = override_get_current_user_1
        try:
            user1_assets_response = test_client.get(
                f"/api/v1/assets/{user1.id}",
                headers={"Authorization": f"Bearer {token1}"},
            )
            assert user1_assets_response.status_code == 200
            user1_assets = user1_assets_response.json()["data"]
            assert len(user1_assets) == 1
            assert user1_assets[0]["value"] == 3000000.0
            assert f"用户{user1.id}的房产" in user1_assets[0]["name"]
        finally:
            app.dependency_overrides.clear()

        # Check user2's assets
        app.dependency_overrides[get_current_user] = override_get_current_user_2
        try:
            user2_assets_response = test_client.get(
                f"/api/v1/assets/{user2.id}",
                headers={"Authorization": f"Bearer {token2}"},
            )
            assert user2_assets_response.status_code == 200
            user2_assets = user2_assets_response.json()["data"]
            assert len(user2_assets) == 1
            assert user2_assets[0]["value"] == 5000000.0
            assert f"用户{user2.id}的房产" in user2_assets[0]["name"]
        finally:
            app.dependency_overrides.clear()


class TestSystemPerformanceAndStability:
    """Test system performance and stability under various conditions"""

    async def test_large_asset_portfolio_handling(
        self, test_client, test_user_with_profile, db_session
    ):
        """Test system performance with large number of assets"""
        user, token = test_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Create 50 assets to test performance
            asset_types = ["real_estate", "cash", "investment", "insurance"]

            for i in range(50):
                asset_type = asset_types[i % len(asset_types)]
                response = test_client.post(
                    f"/api/v1/assets/{user.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "asset_type": asset_type,
                        "name": f"资产{i + 1}",
                        "value": 100000.0 + (i * 10000),
                        "is_confirmed": True,
                        "extra_data": {"index": i},
                    },
                )
                assert response.status_code == 200

            # Verify all assets were created
            assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert assets_response.status_code == 200
            assets_data = assets_response.json()
            assert len(assets_data["data"]) == 50

            # Test portfolio health calculation with large dataset
            health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert health_data["success"] is True

            # Verify calculations are still accurate
            portfolio = health_data["data"]
            assert portfolio["net_worth"] > 0
            assert isinstance(portfolio["real_estate_ratio"], (int, float))
            assert isinstance(portfolio["liquidity_ratio"], (int, float))

        finally:
            app.dependency_overrides.clear()

    async def test_api_response_times(
        self, test_client, test_user_with_profile, db_session
    ):
        """Test that API response times are within acceptable limits"""
        import time

        user, token = test_user_with_profile

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Create a few assets first
            for i in range(5):
                test_client.post(
                    f"/api/v1/assets/{user.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "asset_type": "real_estate",
                        "name": f"房产{i + 1}",
                        "value": 1000000.0 * (i + 1),
                        "is_confirmed": True,
                    },
                )

            # Test response times for key endpoints
            endpoints_to_test = [
                ("GET", f"/api/v1/assets/{user.id}"),
                ("GET", f"/api/v1/assets/{user.id}/portfolio/health"),
                ("GET", f"/api/v1/profiles/{user.id}"),
            ]

            for method, endpoint in endpoints_to_test:
                start_time = time.time()

                if method == "GET":
                    response = test_client.get(
                        endpoint, headers={"Authorization": f"Bearer {token}"}
                    )

                end_time = time.time()
                response_time = end_time - start_time

                # Response should be successful
                assert response.status_code == 200

                # Response time should be under 2 seconds (generous limit for testing)
                assert response_time < 2.0, (
                    f"Endpoint {endpoint} took {response_time:.2f}s"
                )

                logger.info(f"Endpoint {endpoint} response time: {response_time:.3f}s")

        finally:
            app.dependency_overrides.clear()
