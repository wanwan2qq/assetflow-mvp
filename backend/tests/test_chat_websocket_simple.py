"""
Simple WebSocket Chat API Integration Tests
Tests the complete chat flow including WebSocket connections and message processing
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.main import app
from app.models.user import User
from app.services.auth import auth_service

logger = logging.getLogger(__name__)


@pytest.fixture
def test_client():
    """Create test client for WebSocket testing"""
    return TestClient(app)


@pytest.fixture
async def mock_user(db_session: AsyncSession):
    """Create a mock user for testing"""
    user = User(
        phone="13800138000",
        device_id="test-device-123",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = auth_service.create_access_token(user.id)
    return user, token


class TestWebSocketAuthentication:
    """Test WebSocket authentication and connection management"""

    def test_websocket_connection_without_token(self, test_client):
        """Test WebSocket connection fails without authentication token"""
        with pytest.raises((WebSocketException, Exception)):
            with test_client.websocket_connect("/api/v1/chat/ws/chat/1"):
                pass

    def test_websocket_connection_with_invalid_token(self, test_client):
        """Test WebSocket connection fails with invalid token"""
        with pytest.raises((WebSocketException, Exception)):
            with test_client.websocket_connect(
                "/api/v1/chat/ws/chat/1?token=invalid_token"
            ):
                pass


class TestChatContextAPI:
    """Test REST API endpoints for chat context management"""

    @patch("app.api.api_v1.endpoints.chat.get_chat_agent")
    async def test_get_chat_context(
        self, mock_get_agent, test_client, mock_user, db_session
    ):
        """Test getting chat context via REST API"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Mock chat agent with context
            mock_agent = MagicMock()
            mock_context = MagicMock()
            mock_context.user_id = user.id
            mock_context.current_stage = "property_collection"
            mock_context.conversation_history = [{"role": "user", "content": "test"}]
            mock_context.extracted_assets = []
            mock_context.user_profile = None

            mock_agent.get_conversation_context.return_value = mock_context
            mock_get_agent.return_value = mock_agent

            response = test_client.get(
                f"/api/v1/chat/chat/context/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == user.id
            assert data["current_stage"] == "property_collection"
            assert data["conversation_length"] == 1
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @patch("app.api.api_v1.endpoints.chat.get_chat_agent")
    async def test_get_chat_context_no_context(
        self, mock_get_agent, test_client, mock_user, db_session
    ):
        """Test getting chat context when no context exists"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            mock_agent = MagicMock()
            mock_agent.get_conversation_context.return_value = None
            mock_get_agent.return_value = mock_agent

            response = test_client.get(
                f"/api/v1/chat/chat/context/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "No active conversation"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    @patch("app.api.api_v1.endpoints.chat.get_chat_agent")
    async def test_clear_chat_context(
        self, mock_get_agent, test_client, mock_user, db_session
    ):
        """Test clearing chat context via REST API"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            mock_agent = MagicMock()
            mock_agent.clear_conversation_context = MagicMock()
            mock_get_agent.return_value = mock_agent

            response = test_client.delete(
                f"/api/v1/chat/chat/context/{user.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Chat context cleared"

            # Verify the agent method was called
            mock_agent.clear_conversation_context.assert_called_once_with(user.id)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    async def test_chat_context_access_control(
        self, test_client, mock_user, db_session
    ):
        """Test that users can only access their own chat context"""
        user, token = mock_user
        different_user_id = user.id + 1

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Try to access different user's context
            response = test_client.get(
                f"/api/v1/chat/chat/context/{different_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 403
            data = response.json()
            assert data["detail"] == "Access denied"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestChatMessageAPI:
    """Test non-WebSocket chat message API"""

    @patch("app.api.api_v1.endpoints.chat.get_chat_agent")
    async def test_send_chat_message(
        self, mock_get_agent, test_client, mock_user, db_session
    ):
        """Test sending chat message via REST API"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            # Add a profile attribute to avoid lazy loading issues
            user.profile = None
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            # Mock chat agent
            mock_agent = MagicMock()

            async def mock_process_message(message, user_id, profile):
                yield "这是AI的回复。"
                yield "我理解您的需求。"

            mock_agent.process_message = mock_process_message

            # Mock UI component extraction
            mock_ui_component = MagicMock()
            mock_ui_component.model_dump.return_value = {
                "type": "VALUATION_CARD",
                "data": {"price": 5000000},
                "position": 0,
            }
            mock_agent.extract_ui_components.return_value = [mock_ui_component]
            mock_get_agent.return_value = mock_agent

            response = test_client.post(
                "/api/v1/chat/chat/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "我有一套房产需要评估"},
            )

            assert response.status_code == 200
            data = response.json()

            assert "response" in data
            assert "这是AI的回复" in data["response"]
            assert "ui_components" in data
            assert len(data["ui_components"]) == 1
            assert data["ui_components"][0]["type"] == "VALUATION_CARD"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    async def test_send_empty_chat_message(self, test_client, mock_user, db_session):
        """Test sending empty chat message returns error"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = test_client.post(
                "/api/v1/chat/chat/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": ""},
            )

            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Message cannot be empty"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()

    async def test_send_chat_message_whitespace_only(
        self, test_client, mock_user, db_session
    ):
        """Test sending whitespace-only message returns error"""
        user, token = mock_user

        # Override the dependency to return our test user
        def override_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = test_client.post(
                "/api/v1/chat/chat/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": "   \n\t  "},
            )

            assert response.status_code == 400
            data = response.json()
            assert data["detail"] == "Message cannot be empty"
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()


class TestConnectionManager:
    """Test WebSocket connection manager functionality"""

    def test_connection_manager_connect_disconnect(self):
        """Test connection manager basic operations"""
        from app.api.api_v1.endpoints.chat import ConnectionManager

        manager = ConnectionManager()

        # Initially no connections
        assert len(manager.active_connections) == 0

        # Test disconnect
        user_id = 123
        manager.disconnect(user_id)
        assert user_id not in manager.active_connections

        # Test disconnect non-existent connection (should not raise error)
        manager.disconnect(999)

    async def test_connection_manager_send_message(self):
        """Test connection manager message sending"""
        from app.api.api_v1.endpoints.chat import ConnectionManager

        manager = ConnectionManager()

        # Mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        user_id = 123
        manager.active_connections[user_id] = mock_websocket

        # Test sending message
        await manager.send_message(user_id, "test message")
        mock_websocket.send_text.assert_called_once_with("test message")

        # Test sending to non-existent connection (should not raise error)
        await manager.send_message(999, "test message")


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""

    def test_websocket_url_structure(self, test_client):
        """Test that WebSocket URLs are properly structured"""
        # Test that the WebSocket endpoint exists in the router
        from app.api.api_v1.endpoints.chat import router

        # Check that the WebSocket route is registered
        websocket_routes = [
            route
            for route in router.routes
            if hasattr(route, "path") and "ws" in route.path
        ]
        assert len(websocket_routes) > 0

        # Verify the route pattern
        ws_route = websocket_routes[0]
        assert "/ws/chat/{user_id}" in ws_route.path


class TestChatAgentIntegration:
    """Test chat agent integration with WebSocket endpoints"""

    @patch("app.api.api_v1.endpoints.chat.get_chat_agent")
    def test_chat_agent_initialization(self, mock_get_agent):
        """Test that chat agent is properly initialized"""
        mock_agent = MagicMock()
        mock_get_agent.return_value = mock_agent

        # Import the endpoint to trigger agent initialization
        from app.api.api_v1.endpoints.chat import get_chat_agent

        agent = get_chat_agent()
        assert agent is not None
        mock_get_agent.assert_called_once()

    def test_websocket_authenticate_function_exists(self):
        """Test that WebSocket authentication function exists"""
        from app.api.api_v1.endpoints.chat import authenticate_websocket

        # Function should exist and be callable
        assert callable(authenticate_websocket)

    def test_connection_manager_singleton(self):
        """Test that connection manager is properly instantiated"""
        from app.api.api_v1.endpoints.chat import manager

        # Manager should be instantiated
        assert manager is not None
        assert hasattr(manager, "active_connections")
        assert hasattr(manager, "connect")
        assert hasattr(manager, "disconnect")
        assert hasattr(manager, "send_message")
