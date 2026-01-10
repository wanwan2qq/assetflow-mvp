"""
Integration tests for authentication system
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.database import get_db_session
from app.main import app
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create async test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    # Import all models to ensure they're registered with SQLModel
    from app.models.audit import AuditLog, UserAssetHistory  # noqa: F401
    from app.models.chat import ChatSession  # noqa: F401
    from app.models.commercial import CommercialProduct  # noqa: F401
    from app.models.interaction import UserInteraction  # noqa: F401
    from app.models.user import User, UserAsset, UserProfile  # noqa: F401

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    """Create async test database session"""
    AsyncSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session):
    """Create test client with async test database"""

    async def get_test_session():
        yield test_session

    app.dependency_overrides[get_db_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAuthenticationSystem:
    """Test authentication system functionality"""

    @pytest.mark.asyncio
    async def test_phone_login_creates_new_user(self, test_client):
        """Test that phone login creates new user if doesn't exist"""
        response = test_client.post(
            "/api/v1/auth/login/phone",
            json={"phone": "13800138000", "verification_code": "123456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["phone"] == "13800138000"
        assert data["user_id"] > 0

    @pytest.mark.asyncio
    async def test_phone_login_existing_user(self, test_client, test_session):
        """Test that phone login works with existing user"""
        # Create existing user
        user = User(phone="13800138001", device_id="test_device")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        response = test_client.post(
            "/api/v1/auth/login/phone",
            json={"phone": "13800138001", "verification_code": "123456"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert data["phone"] == "13800138001"

    @pytest.mark.asyncio
    async def test_device_login_creates_anonymous_user(self, test_client):
        """Test that device login creates anonymous user"""
        response = test_client.post(
            "/api/v1/auth/login/device", json={"device_id": "test_device_123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["device_id"] == "test_device_123"
        assert data["phone"].startswith("anonymous_")

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, test_client):
        """Test that protected endpoints require authentication"""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, test_client):
        """Test that protected endpoints work with valid token"""
        # First login to get token
        login_response = test_client.post(
            "/api/v1/auth/login/phone",
            json={"phone": "13800138002", "verification_code": "123456"},
        )
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        response = test_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "13800138002"

    @pytest.mark.asyncio
    async def test_user_data_isolation(self, test_client, test_session):
        """Test that users can only access their own data"""
        # Create two users
        user1 = User(phone="13800138003", device_id="device1")
        user2 = User(phone="13800138004", device_id="device2")
        test_session.add(user1)
        test_session.add(user2)
        await test_session.commit()
        await test_session.refresh(user1)
        await test_session.refresh(user2)

        # Login as user1
        login_response = test_client.post(
            "/api/v1/auth/login/phone",
            json={"phone": "13800138003", "verification_code": "123456"},
        )
        token = login_response.json()["access_token"]

        # Try to access user2's assets (should fail)
        response = test_client.get(
            f"/api/v1/assets/{user2.id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_bind_phone_to_anonymous_user(self, test_client):
        """Test binding phone number to anonymous user"""
        # First login anonymously
        device_response = test_client.post(
            "/api/v1/auth/login/device", json={"device_id": "test_device_456"}
        )
        token = device_response.json()["access_token"]

        # Bind phone number
        bind_response = test_client.post(
            "/api/v1/auth/bind-phone",
            json={"phone": "13800138005", "verification_code": "123456"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert bind_response.status_code == 200
        data = bind_response.json()
        assert data["phone"] == "13800138005"
        assert data["device_id"] == "test_device_456"

    @pytest.mark.asyncio
    async def test_invalid_verification_code_format(self, test_client):
        """Test that invalid verification code format is rejected"""
        response = test_client.post(
            "/api/v1/auth/login/phone",
            json={
                "phone": "13800138006",
                "verification_code": "123",  # Too short
            },
        )

        assert response.status_code == 422
        assert "verification_code" in str(response.json())

    @pytest.mark.asyncio
    async def test_token_refresh(self, test_client):
        """Test token refresh functionality"""
        # Login to get initial token
        login_response = test_client.post(
            "/api/v1/auth/login/phone",
            json={"phone": "13800138007", "verification_code": "123456"},
        )
        token = login_response.json()["access_token"]

        # Refresh token
        refresh_response = test_client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"}
        )

        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        assert new_token != token  # Should be a new token
