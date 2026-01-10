"""
Simple integration test to verify WebSocket functionality
"""

import pytest
from fastapi import WebSocketException
from fastapi.testclient import TestClient

from app.main import app


def test_websocket_endpoint_exists():
    """Test that WebSocket endpoint is registered"""
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


def test_websocket_connection_without_token():
    """Test WebSocket connection fails without authentication token"""
    client = TestClient(app)

    with pytest.raises((WebSocketException, Exception)):
        with client.websocket_connect("/api/v1/chat/ws/chat/1"):
            pass


def test_connection_manager_exists():
    """Test that connection manager is properly instantiated"""
    from app.api.api_v1.endpoints.chat import manager

    # Manager should be instantiated
    assert manager is not None
    assert hasattr(manager, "active_connections")
    assert hasattr(manager, "connect")
    assert hasattr(manager, "disconnect")
    assert hasattr(manager, "send_message")
