"""
Authentication service for AssetFlow
Handles JWT token generation, validation, and user authentication
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.models.user import User


class AuthService:
    """Authentication service for user management and JWT tokens"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(
        self, user_id: int, expires_delta: timedelta | None = None
    ) -> str:
        """Create JWT access token for user"""
        now = datetime.utcnow()
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(
                minutes=self.access_token_expire_minutes
            )

        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": now,
            "type": "access",
            # Add microseconds to ensure unique tokens
            "jti": str(now.timestamp()),
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> int | None:
        """Verify JWT token and return user_id if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                return None

            return int(user_id)
        except (JWTError, ValueError):
            return None

    async def authenticate_user_by_phone(self, session: AsyncSession, phone: str) -> User | None:
        """Authenticate user by phone number (for SMS login)"""
        statement = select(User).where(User.phone == phone)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        return user

    async def authenticate_user_by_device(
        self, session: AsyncSession, device_id: str
    ) -> User | None:
        """Authenticate user by device ID (for anonymous login)"""
        statement = select(User).where(User.device_id == device_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        return user

    async def create_user_by_phone(
        self, session: AsyncSession, phone: str, device_id: str | None = None
    ) -> User:
        """Create new user with phone number"""
        user = User(phone=phone, device_id=device_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def create_user_by_device(self, session: AsyncSession, device_id: str) -> User:
        """Create new anonymous user with device ID"""
        # Generate a numeric phone number for anonymous users to satisfy check constraint
        # Use hash of device_id to create a consistent 11-digit number
        import hashlib
        device_hash = hashlib.md5(device_id.encode()).hexdigest()
        # Convert first 10 hex chars to a number and ensure it's 11 digits
        hash_int = int(device_hash[:10], 16)
        anonymous_phone = f"1{hash_int % 10000000000:010d}"  # Ensure 11 digits starting with 1
        
        user = User(phone=anonymous_phone, device_id=device_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def bind_phone_to_user(
        self, session: AsyncSession, user_id: int, phone: str
    ) -> User | None:
        """Bind phone number to existing anonymous user"""
        user = await session.get(User, user_id)
        if not user:
            return None

        # Check if phone is already taken
        existing_user = await self.authenticate_user_by_phone(session, phone)
        if existing_user and existing_user.id != user_id:
            return None

        user.phone = phone
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# Global auth service instance
auth_service = AuthService()
