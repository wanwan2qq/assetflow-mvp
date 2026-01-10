"""
Database configuration and session management
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine

from app.core.config import settings

# Create sync engine for migrations
sync_engine = create_engine(settings.database_url, echo=True)

# Determine async database URL based on the database type
if settings.database_url.startswith("sqlite"):
    # Handle both sqlite:// and sqlite+aiosqlite:// formats
    if "aiosqlite" in settings.database_url:
        async_database_url = settings.database_url
    else:
        async_database_url = settings.database_url.replace(
            "sqlite://", "sqlite+aiosqlite://"
        )
else:
    async_database_url = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

# Create async engine for application
async_engine = create_async_engine(
    async_database_url,
    echo=True,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    # Import all models here to ensure they are registered with SQLModel
    from app.models.audit import AuditLog, UserAssetHistory  # noqa: F401
    from app.models.chat import ChatSession  # noqa: F401
    from app.models.commercial import CommercialProduct  # noqa: F401
    from app.models.interaction import UserInteraction  # noqa: F401
    from app.models.user import User, UserAsset, UserProfile  # noqa: F401

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
