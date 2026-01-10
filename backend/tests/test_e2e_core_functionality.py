"""
End-to-End Core Functionality Tests
Tests the essential user journey that we know works
"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.main import app
from app.models.user import User
from app.services.auth import auth_service

logger = logging.getLogger(__name__)


@pytest.fixture
def test_client():
    """Create test client for E2E testing"""
    return TestClient(app)


@pytest.fixture
async def e2e_test_user(db_session: AsyncSession):
    """Create a test user for E2E testing"""
    user = User(
        phone="13800138999",
        device_id="e2e-core-test",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = auth_service.create_access_token(user.id)
    return user, token


class TestCoreUserJourney:
    """Test core user journey that we know works"""

    async def test_complete_asset_management_flow(
        self, test_client, e2e_test_user, db_session
    ):
        """Test complete asset management flow"""
        user, token = e2e_test_user

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            logger.info("Starting core asset management flow test")

            # === Phase 1: Create diverse asset portfolio ===
            logger.info("Phase 1: Creating asset portfolio")

            assets_to_create = [
                {
                    "asset_type": "real_estate",
                    "name": "北京朝阳区住宅",
                    "value": 6000000.0,
                    "extra_data": {"area": 120.0, "city": "北京"},
                },
                {
                    "asset_type": "cash",
                    "name": "银行存款",
                    "value": 500000.0,
                    "extra_data": {"account_type": "savings"},
                },
                {
                    "asset_type": "investment",
                    "name": "股票投资",
                    "value": 800000.0,
                    "extra_data": {"investment_type": "stocks"},
                },
                {
                    "asset_type": "investment",
                    "name": "基金投资",
                    "value": 400000.0,
                    "extra_data": {"investment_type": "funds"},
                },
                {
                    "asset_type": "insurance",
                    "name": "人寿保险",
                    "value": 1000000.0,
                    "extra_data": {"insurance_type": "life"},
                },
                {
                    "asset_type": "liability",
                    "name": "房贷",
                    "value": 3000000.0,
                    "extra_data": {"loan_type": "mortgage"},
                },
            ]

            created_assets = []
            for asset_data in assets_to_create:
                response = test_client.post(
                    f"/api/v1/assets/{user.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={**asset_data, "is_confirmed": True},
                )
                assert response.status_code == 200, (
                    f"Failed to create {asset_data['name']}"
                )
                created_assets.append(response.json()["data"])

            assert len(created_assets) == 6
            logger.info(f"Created {len(created_assets)} assets successfully")

            # === Phase 2: Verify asset retrieval ===
            logger.info("Phase 2: Verifying asset retrieval")

            assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert assets_response.status_code == 200
            assets_data = assets_response.json()
            assert assets_data["success"] is True
            assert len(assets_data["data"]) == 6

            # Verify asset types
            asset_types = [asset["asset_type"] for asset in assets_data["data"]]
            expected_types = [
                "real_estate",
                "cash",
                "investment",
                "investment",
                "insurance",
                "liability",
            ]
            for expected_type in expected_types:
                assert expected_type in asset_types

            # === Phase 3: Portfolio health analysis ===
            logger.info("Phase 3: Portfolio health analysis")

            health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert health_response.status_code == 200
            health_data = health_response.json()
            assert health_data["success"] is True

            portfolio = health_data["data"]

            # Verify calculations
            # Total assets: 6M + 0.5M + 0.8M + 0.4M + 1M = 8.7M
            # Total liabilities: 3M
            # Net worth: 8.7M - 3M = 5.7M
            expected_net_worth = 5700000.0
            assert abs(portfolio["net_worth"] - expected_net_worth) < 1000

            # Real estate ratio: 6M / 5.7M ≈ 105%
            assert portfolio["real_estate_ratio"] > 1.0

            # Should have risk warnings
            assert isinstance(portfolio["risk_warnings"], list)

            logger.info(
                f"Portfolio analysis: Net worth={portfolio['net_worth']:,.0f}, RE ratio={portfolio['real_estate_ratio']:.1%}"
            )

            # === Phase 4: Asset updates ===
            logger.info("Phase 4: Testing asset updates")

            # Update the real estate asset value
            real_estate_asset = next(
                asset
                for asset in assets_data["data"]
                if asset["asset_type"] == "real_estate"
            )

            update_response = test_client.put(
                f"/api/v1/assets/{user.id}/{real_estate_asset['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "value": 6500000.0,  # Increased value
                    "extra_data": {
                        "area": 120.0,
                        "city": "北京",
                        "updated_reason": "市场价格上涨",
                    },
                },
            )
            assert update_response.status_code == 200

            # Verify updated portfolio
            updated_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert updated_health_response.status_code == 200
            updated_health = updated_health_response.json()["data"]

            # Net worth should be higher: 5.7M + 0.5M = 6.2M
            assert updated_health["net_worth"] > portfolio["net_worth"]

            # === Phase 5: Chat integration ===
            logger.info("Phase 5: Testing chat integration")

            with patch(
                "app.api.api_v1.endpoints.chat.get_chat_agent"
            ) as mock_get_agent:
                mock_agent = MagicMock()

                # Mock AI response
                async def mock_analysis_response(message, user_id, profile):
                    yield "根据您的资产分析，您的净资产为 "
                    yield f"{updated_health['net_worth']:,.0f} 元。\n\n"
                    yield "主要发现：\n"
                    yield f"1. 房产占比 {updated_health['real_estate_ratio']:.1%}，建议适当分散投资\n"
                    yield "2. 现金储备充足，流动性良好\n"
                    yield "3. 已有基础保险保障\n\n"
                    yield "<WIDGET:PORTFOLIO_CHART>\n\n"
                    yield "建议考虑增加股票和基金投资比例。"

                mock_agent.process_message = mock_analysis_response

                # Mock UI components
                mock_ui_components = [
                    MagicMock(
                        model_dump=lambda: {
                            "type": "PORTFOLIO_CHART",
                            "data": {"chart_type": "pie"},
                            "position": 0,
                        }
                    )
                ]
                mock_agent.extract_ui_components.return_value = mock_ui_components
                mock_get_agent.return_value = mock_agent

                # Send chat message
                chat_response = test_client.post(
                    "/api/v1/chat/chat/message",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"message": "请分析我的资产配置"},
                )

                assert chat_response.status_code == 200
                chat_data = chat_response.json()

                # Verify response contains analysis
                response_text = chat_data["response"]
                assert "净资产" in response_text
                assert "房产占比" in response_text
                assert "PORTFOLIO_CHART" in response_text

                # Verify UI components
                assert len(chat_data["ui_components"]) == 1
                assert chat_data["ui_components"][0]["type"] == "PORTFOLIO_CHART"

            # === Phase 6: Asset deletion ===
            logger.info("Phase 6: Testing asset deletion")

            # Delete one of the investment assets
            investment_asset = next(
                asset
                for asset in assets_data["data"]
                if asset["asset_type"] == "investment" and "基金" in asset["name"]
            )

            delete_response = test_client.delete(
                f"/api/v1/assets/{user.id}/{investment_asset['id']}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert delete_response.status_code == 200

            # Verify asset was deleted
            final_assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert final_assets_response.status_code == 200
            final_assets = final_assets_response.json()["data"]
            assert len(final_assets) == 5  # One less asset

            # Verify deleted asset is not in the list
            asset_ids = [asset["id"] for asset in final_assets]
            assert investment_asset["id"] not in asset_ids

            # === Phase 7: Performance verification ===
            logger.info("Phase 7: Performance verification")

            # Test multiple rapid requests
            start_time = time.time()

            for _ in range(5):
                perf_response = test_client.get(
                    f"/api/v1/assets/{user.id}/portfolio/health",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert perf_response.status_code == 200

            total_time = time.time() - start_time
            assert total_time < 3.0  # Should complete within 3 seconds

            avg_time = total_time / 5
            logger.info(f"Average portfolio health calculation time: {avg_time:.3f}s")

            logger.info("✅ Complete core asset management flow test passed!")

        finally:
            app.dependency_overrides.clear()

    async def test_error_handling_and_recovery(
        self, test_client, e2e_test_user, db_session
    ):
        """Test error handling and recovery scenarios"""
        user, token = e2e_test_user

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            logger.info("Starting error handling and recovery test")

            # Test 1: Invalid asset creation
            invalid_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "invalid_type",
                    "name": "Invalid Asset",
                    "value": -1000.0,  # Negative value
                    "is_confirmed": True,
                },
            )
            assert invalid_response.status_code == 422  # Validation error

            # Test 2: Access control
            different_user_id = user.id + 999
            unauthorized_response = test_client.get(
                f"/api/v1/assets/{different_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert unauthorized_response.status_code == 403

            # Test 3: Non-existent asset update
            nonexistent_response = test_client.put(
                f"/api/v1/assets/{user.id}/99999",
                headers={"Authorization": f"Bearer {token}"},
                json={"value": 100000.0},
            )
            assert nonexistent_response.status_code == 404

            # Test 4: Invalid authentication
            invalid_auth_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": "Bearer invalid_token"},
            )
            assert invalid_auth_response.status_code == 401

            # Test 5: Recovery after errors - normal operations should still work
            valid_asset_response = test_client.post(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "asset_type": "cash",
                    "name": "Recovery Test Asset",
                    "value": 50000.0,
                    "is_confirmed": True,
                },
            )
            assert valid_asset_response.status_code == 200

            logger.info("✅ Error handling and recovery test passed!")

        finally:
            app.dependency_overrides.clear()

    async def test_data_consistency_verification(
        self, test_client, e2e_test_user, db_session
    ):
        """Test data consistency across operations"""
        user, token = e2e_test_user

        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            logger.info("Starting data consistency verification test")

            # Create initial assets
            initial_assets = [
                {"asset_type": "real_estate", "name": "房产1", "value": 2000000.0},
                {"asset_type": "cash", "name": "现金1", "value": 300000.0},
                {"asset_type": "liability", "name": "负债1", "value": 1000000.0},
            ]

            created_ids = []
            for asset_data in initial_assets:
                response = test_client.post(
                    f"/api/v1/assets/{user.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={**asset_data, "is_confirmed": True},
                )
                assert response.status_code == 200
                created_ids.append(response.json()["data"]["id"])

            # Get initial portfolio health
            initial_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert initial_health_response.status_code == 200
            initial_health = initial_health_response.json()["data"]

            # Expected: (2M + 0.3M) - 1M = 1.3M net worth
            expected_net_worth = 1300000.0
            assert abs(initial_health["net_worth"] - expected_net_worth) < 1000

            # Update asset values
            update_response = test_client.put(
                f"/api/v1/assets/{user.id}/{created_ids[0]}",  # Real estate
                headers={"Authorization": f"Bearer {token}"},
                json={"value": 2200000.0},  # Increase by 200k
            )
            assert update_response.status_code == 200

            # Verify portfolio health reflects the change
            updated_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert updated_health_response.status_code == 200
            updated_health = updated_health_response.json()["data"]

            # Should be 200k higher: 1.3M + 0.2M = 1.5M
            expected_updated_net_worth = 1500000.0
            assert abs(updated_health["net_worth"] - expected_updated_net_worth) < 1000

            # Delete an asset
            delete_response = test_client.delete(
                f"/api/v1/assets/{user.id}/{created_ids[1]}",  # Cash
                headers={"Authorization": f"Bearer {token}"},
            )
            assert delete_response.status_code == 200

            # Verify portfolio health reflects the deletion
            final_health_response = test_client.get(
                f"/api/v1/assets/{user.id}/portfolio/health",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert final_health_response.status_code == 200
            final_health = final_health_response.json()["data"]

            # Should be 300k lower: 1.5M - 0.3M = 1.2M
            expected_final_net_worth = 1200000.0
            assert abs(final_health["net_worth"] - expected_final_net_worth) < 1000

            # Verify asset count
            final_assets_response = test_client.get(
                f"/api/v1/assets/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert final_assets_response.status_code == 200
            final_assets = final_assets_response.json()["data"]
            assert len(final_assets) == 2  # Real estate + liability

            logger.info("✅ Data consistency verification test passed!")

        finally:
            app.dependency_overrides.clear()
