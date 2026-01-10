"""
Unit tests for authentication service
"""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.services.auth import AuthService


class TestAuthService:
    """Test authentication service functionality"""

    @pytest.fixture
    def auth_service(self):
        """Create auth service instance"""
        return AuthService()

    @pytest_asyncio.fixture
    async def test_session(self):
        """Create async test database session"""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        AsyncSessionLocal = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.rollback()
                await session.close()

        await engine.dispose()

    def test_create_access_token(self, auth_service):
        """Test JWT token creation"""
        user_id = 123
        token = auth_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        decoded_user_id = auth_service.verify_token(token)
        assert decoded_user_id == user_id

    def test_verify_valid_token(self, auth_service):
        """Test token verification with valid token"""
        user_id = 456
        token = auth_service.create_access_token(user_id)

        verified_user_id = auth_service.verify_token(token)
        assert verified_user_id == user_id

    def test_verify_invalid_token(self, auth_service):
        """Test token verification with invalid token"""
        invalid_token = "invalid.token.here"

        verified_user_id = auth_service.verify_token(invalid_token)
        assert verified_user_id is None

    def test_verify_expired_token(self, auth_service):
        """Test token verification with expired token"""
        user_id = 789
        # Create token that expires immediately
        expired_delta = timedelta(seconds=-1)
        token = auth_service.create_access_token(user_id, expired_delta)

        verified_user_id = auth_service.verify_token(token)
        assert verified_user_id is None

    @pytest.mark.asyncio
    async def test_create_user_by_phone(self, auth_service, test_session):
        """Test creating user with phone number"""
        phone = "13800138000"
        device_id = "test_device"

        user = await auth_service.create_user_by_phone(test_session, phone, device_id)

        assert user.id is not None
        assert user.phone == phone
        assert user.device_id == device_id
        assert isinstance(user.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_user_by_device(self, auth_service, test_session):
        """Test creating anonymous user with device ID"""
        device_id = "test_device_123"

        user = await auth_service.create_user_by_device(test_session, device_id)

        assert user.id is not None
        assert user.phone.startswith("anonymous_")
        assert user.device_id == device_id

    @pytest.mark.asyncio
    async def test_authenticate_user_by_phone(self, auth_service, test_session):
        """Test authenticating user by phone number"""
        phone = "13800138001"

        # Create user first
        created_user = await auth_service.create_user_by_phone(test_session, phone)

        # Authenticate user
        authenticated_user = await auth_service.authenticate_user_by_phone(
            test_session, phone
        )

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.phone == phone

    @pytest.mark.asyncio
    async def test_authenticate_user_by_device(self, auth_service, test_session):
        """Test authenticating user by device ID"""
        device_id = "test_device_456"

        # Create user first
        created_user = await auth_service.create_user_by_device(test_session, device_id)

        # Authenticate user
        authenticated_user = await auth_service.authenticate_user_by_device(
            test_session, device_id
        )

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.device_id == device_id

    @pytest.mark.asyncio
    async def test_bind_phone_to_user(self, auth_service, test_session):
        """Test binding phone number to existing user"""
        device_id = "test_device_789"
        phone = "13800138002"

        # Create anonymous user
        user = await auth_service.create_user_by_device(test_session, device_id)
        original_phone = user.phone

        # Bind phone number
        updated_user = await auth_service.bind_phone_to_user(test_session, user.id, phone)

        assert updated_user is not None
        assert updated_user.id == user.id
        assert updated_user.phone == phone
        assert updated_user.phone != original_phone
        assert updated_user.device_id == device_id

    @pytest.mark.asyncio
    async def test_bind_phone_to_nonexistent_user(self, auth_service, test_session):
        """Test binding phone to non-existent user returns None"""
        nonexistent_user_id = 99999
        phone = "13800138003"

        result = await auth_service.bind_phone_to_user(
            test_session, nonexistent_user_id, phone
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_bind_phone_already_taken(self, auth_service, test_session):
        """Test binding phone that's already taken by another user"""
        phone = "13800138004"

        # Create first user with phone
        await auth_service.create_user_by_phone(test_session, phone)

        # Create second anonymous user
        user2 = await auth_service.create_user_by_device(test_session, "device_123")

        # Try to bind same phone to second user
        result = await auth_service.bind_phone_to_user(test_session, user2.id, phone)

        assert result is None

    def test_token_contains_correct_claims(self, auth_service):
        """Test that JWT token contains correct claims"""
        from jose import jwt

        user_id = 999
        token = auth_service.create_access_token(user_id)

        # Decode without verification to check claims
        payload = jwt.get_unverified_claims(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
