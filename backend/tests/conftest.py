"""
Test configuration and fixtures
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.database import get_db_session
from app.main import app
from app.models.audit import AuditLog, UserAssetHistory  # noqa: F401
from app.models.chat import ChatSession  # noqa: F401
from app.models.commercial import CommercialProduct  # noqa: F401
from app.models.interaction import UserInteraction  # noqa: F401
from app.models.user import User, UserAsset, UserProfile  # noqa: F401

# Set test environment variables before importing anything else
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_MOCK_SEARCH"] = "true"


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for testing"""
    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
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


@pytest.fixture(scope="function")
def test_client():
    """Create synchronous test client for simple tests"""
    return TestClient(app)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        phone="13800138000",
        device_id="test-device-123",
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    yield loop
    loop.close()
