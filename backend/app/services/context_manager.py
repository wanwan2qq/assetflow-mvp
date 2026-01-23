"""
Context Manager - Centralized context management for conversations

This module replaces the scattered context handling in ChatAgent,
providing a clean interface for:
1. Reading/writing conversation context
2. Caching (memory or Redis)
3. Database persistence
4. Handling JSON field ORM issues (flag_modified)

AI Coding Guidance:
- All context reads/writes should go through this module
- Never directly manipulate UserCognition.collection_status elsewhere
- Cache invalidation happens automatically on writes
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_db_session
from app.models.cognition import UserCognition
from app.models.context import ConversationContext, ContextUpdate
from app.models.user import UserAsset, UserProfile

logger = logging.getLogger(__name__)


class CacheBackend:
    """Abstract cache backend interface."""
    
    async def get(self, key: str) -> Any:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        raise NotImplementedError
    
    async def delete(self, key: str) -> None:
        raise NotImplementedError
    
    async def close(self) -> None:
        """Close the connection (for cleanup)."""
        pass


class InMemoryCache(CacheBackend):
    """Simple in-memory cache for development."""
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
    
    async def get(self, key: str) -> Any:
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.utcnow() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)


class RedisCache(CacheBackend):
    """
    Redis cache backend for production.
    
    Requires redis package and REDIS_URL in settings.
    Falls back to InMemoryCache if Redis is not available.
    """
    
    def __init__(self, redis_url: str | None = None):
        self._redis = None
        self._redis_url = redis_url or getattr(settings, 'REDIS_URL', None)
        self._fallback = InMemoryCache()
        self._initialized = False
    
    async def _ensure_connection(self) -> bool:
        """Ensure Redis connection is established."""
        if self._initialized:
            return self._redis is not None
        
        self._initialized = True
        
        if not self._redis_url:
            logger.warning("REDIS_URL not configured, using in-memory cache fallback")
            return False
        
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info("✅ Redis cache connected")
            return True
        except ImportError:
            logger.warning("redis package not installed, using in-memory cache fallback")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory cache fallback")
            return False
    
    async def get(self, key: str) -> Any:
        if await self._ensure_connection() and self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        return await self._fallback.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        if await self._ensure_connection() and self._redis:
            try:
                # For ConversationContext, serialize to dict first
                if hasattr(value, 'model_dump'):
                    data = json.dumps(value.model_dump(), default=str)
                else:
                    data = json.dumps(value, default=str)
                await self._redis.setex(key, ttl, data)
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        await self._fallback.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        if await self._ensure_connection() and self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        await self._fallback.delete(key)
    
    async def close(self) -> None:
        if self._redis:
            await self._redis.close()


class ContextManager:
    """
    Centralized context management for conversations.
    
    Replaces the Plan E workaround (_refresh_context_from_db) with
    a proper caching and invalidation strategy.
    
    Features:
    - Read-through cache: DB -> Cache -> Return
    - Write-through: Update DB -> Invalidate Cache
    - Force refresh: Bypass cache after extraction (Stale Context fix)
    - Encapsulates ORM JSON field handling
    """
    
    # Cache TTL in seconds (30 minutes)
    CACHE_TTL = 1800
    
    def __init__(self, cache_backend: CacheBackend | None = None):
        """
        Initialize ContextManager.
        
        Args:
            cache_backend: Optional cache backend (defaults based on settings)
        """
        if cache_backend:
            self.cache = cache_backend
        elif getattr(settings, 'REDIS_URL', None):
            self.cache = RedisCache()
        else:
            self.cache = InMemoryCache()
        
        # Fast in-memory cache (always available)
        self._context_cache: dict[int, ConversationContext] = {}
        
        # Track when context was last loaded from DB
        self._load_timestamps: dict[int, datetime] = {}
        
        logger.info(f"✅ ContextManager initialized with {type(self.cache).__name__}")
    
    def _cache_key(self, user_id: int) -> str:
        """Generate cache key for a user."""
        return f"context:user:{user_id}"
    
    async def get_context(self, user_id: int, force_refresh: bool = False) -> ConversationContext:
        """
        Get conversation context for a user.
        
        Strategy:
        1. If force_refresh=True, skip cache and load from DB
        2. Check in-memory cache first (fastest)
        3. Check distributed cache (if configured)
        4. Load from database
        5. Update caches
        
        Args:
            user_id: User ID
            force_refresh: If True, bypass cache and load fresh from DB
            
        Returns:
            ConversationContext with all data loaded
        """
        # Force refresh bypasses all caches (Stale Context fix)
        if force_refresh:
            logger.info(f"🔄 Force refreshing context for user {user_id}")
            context = await self._load_context_from_db(user_id)
            self._context_cache[user_id] = context
            await self.cache.set(self._cache_key(user_id), context, self.CACHE_TTL)
            self._load_timestamps[user_id] = datetime.utcnow()
            return context
        
        # 1. Check in-memory cache
        if user_id in self._context_cache:
            logger.debug(f"Context cache hit (memory) for user {user_id}")
            return self._context_cache[user_id]
        
        # 2. Check distributed cache
        cache_key = self._cache_key(user_id)
        cached = await self.cache.get(cache_key)
        if cached:
            if isinstance(cached, dict):
                # Deserialize from Redis JSON
                context = ConversationContext(**cached)
            elif isinstance(cached, ConversationContext):
                context = cached
            else:
                context = None
            
            if context:
                self._context_cache[user_id] = context
                logger.debug(f"Context cache hit (distributed) for user {user_id}")
                return context
        
        # 3. Load from database
        context = await self._load_context_from_db(user_id)
        
        # 4. Update caches
        self._context_cache[user_id] = context
        await self.cache.set(cache_key, context, self.CACHE_TTL)
        self._load_timestamps[user_id] = datetime.utcnow()
        
        logger.info(f"Context loaded from DB for user {user_id}")
        return context
    
    async def get_fresh_context(self, user_id: int) -> ConversationContext:
        """
        Get fresh context directly from database.
        
        This is the CRITICAL method for solving Stale Context problem.
        Should be called after extraction completes to ensure AI sees latest data.
        
        Args:
            user_id: User ID
            
        Returns:
            Fresh ConversationContext from database
        """
        return await self.get_context(user_id, force_refresh=True)
    
    async def _load_context_from_db(self, user_id: int) -> ConversationContext:
        """
        Load full context from database.
        
        This consolidates the _refresh_context_from_db logic.
        """
        context = ConversationContext(user_id=user_id)
        
        try:
            async for session in get_db_session():
                # Load UserProfile
                profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                profile_result = await session.execute(profile_stmt)
                profile = profile_result.scalar_one_or_none()
                
                if profile:
                    context.user_profile = {
                        "age_range": profile.age_range,
                        "family_structure": profile.family_structure,
                        "risk_preference": profile.risk_preference.value if profile.risk_preference else None,
                        "monthly_expense": profile.monthly_expense,
                        "occupation": profile.occupation,
                        "income_range": profile.income_range,
                    }
                
                # Load UserAssets
                assets_stmt = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_stmt)
                assets = assets_result.scalars().all()
                
                context.extracted_assets = [
                    {
                        "id": asset.id,
                        "type": asset.asset_type.value,
                        "name": asset.name,
                        "value": asset.value,
                        "is_confirmed": asset.is_confirmed,
                        "extra_data": asset.extra_data,
                    }
                    for asset in assets
                ]
                
                # Load RealEstateAssets (detailed property data)
                try:
                    from app.models.real_estate import RealEstateAsset
                    re_stmt = select(RealEstateAsset).where(RealEstateAsset.user_id == user_id)
                    re_result = await session.execute(re_stmt)
                    real_estates = re_result.scalars().all()
                    
                    context.real_estate_assets = [
                        {
                            "id": re.id,
                            "name": re.name,
                            "city": re.city,
                            "district": re.district,
                            "area": re.area,
                            "current_value": re.current_value,
                            "loan_balance": re.loan_balance,
                            "monthly_payment": re.monthly_payment,
                            "loan_type": re.loan_type,
                            "usage": re.usage,
                            "mortgage_potential": re.mortgage_potential,
                        }
                        for re in real_estates
                    ]
                except Exception as e:
                    logger.warning(f"Could not load RealEstateAssets: {e}")
                    context.real_estate_assets = []
                
                # Load UserCognition
                cognition_stmt = select(UserCognition).where(UserCognition.user_id == user_id)
                cognition_result = await session.execute(cognition_stmt)
                cognition = cognition_result.scalar_one_or_none()
                
                if cognition:
                    context.cognition = {
                        "financial_goals": cognition.financial_goals,
                        "risk_profile": cognition.risk_profile,
                        "collection_status": cognition.collection_status,
                        "advisor_note": cognition.advisor_note,
                    }
                    
                    # Update stage based on collection status
                    if cognition.collection_status:
                        collected_count = sum(1 for v in cognition.collection_status.values() if v)
                        if collected_count == 0:
                            context.current_stage = "initial"
                        elif collected_count <= 2:
                            context.current_stage = "property_collection"
                        elif collected_count <= 4:
                            context.current_stage = "asset_collection"
                        else:
                            context.current_stage = "analysis"
                
                break  # Exit async generator
                
        except Exception as e:
            logger.error(f"Error loading context from DB: {e}")
        
        return context
    
    async def update_context(
        self, 
        user_id: int, 
        updates: ContextUpdate
    ) -> None:
        """
        Update context with new data.
        
        This handles:
        1. Database updates (with proper flag_modified for JSON fields)
        2. Cache invalidation
        
        Args:
            user_id: User ID
            updates: ContextUpdate with fields to update
        """
        try:
            async for session in get_db_session():
                # Handle cognition updates (with flag_modified for JSON)
                if updates.cognition_updates:
                    cognition_stmt = select(UserCognition).where(UserCognition.user_id == user_id)
                    cognition_result = await session.execute(cognition_stmt)
                    cognition = cognition_result.scalar_one_or_none()
                    
                    if not cognition:
                        cognition = UserCognition(user_id=user_id)
                        session.add(cognition)
                    
                    # Update collection_status (JSON field - needs flag_modified)
                    if "collection_status" in updates.cognition_updates:
                        if not cognition.collection_status:
                            cognition.collection_status = {}
                        cognition.collection_status.update(updates.cognition_updates["collection_status"])
                        flag_modified(cognition, "collection_status")
                    
                    # Update risk_profile (JSON field - needs flag_modified)
                    if "risk_profile" in updates.cognition_updates:
                        if not cognition.risk_profile:
                            cognition.risk_profile = {}
                        cognition.risk_profile.update(updates.cognition_updates["risk_profile"])
                        flag_modified(cognition, "risk_profile")
                    
                    # Update financial_goals (JSON field - needs flag_modified)
                    if "financial_goals" in updates.cognition_updates:
                        if not cognition.financial_goals:
                            cognition.financial_goals = []
                        goals = updates.cognition_updates["financial_goals"]
                        if isinstance(goals, list):
                            cognition.financial_goals = goals
                        flag_modified(cognition, "financial_goals")
                    
                    # Update other fields
                    if "advisor_note" in updates.cognition_updates:
                        cognition.advisor_note = updates.cognition_updates["advisor_note"]
                    
                    cognition.updated_at = datetime.utcnow()
                    await session.flush()
                
                await session.commit()
                break  # Exit async generator
                
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            raise
        
        # Invalidate caches
        await self.invalidate(user_id)
    
    async def invalidate(self, user_id: int) -> None:
        """
        Invalidate context cache for a user.
        
        Should be called after:
        - Asset extraction completes
        - User profile updates
        - Any database write that affects context
        """
        # Clear in-memory cache
        self._context_cache.pop(user_id, None)
        self._load_timestamps.pop(user_id, None)
        
        # Clear distributed cache
        cache_key = self._cache_key(user_id)
        await self.cache.delete(cache_key)
        
        logger.info(f"🗑️ Context invalidated for user {user_id}")
    
    def get_cached_context(self, user_id: int) -> ConversationContext | None:
        """
        Get cached context without DB fallback.
        
        Useful for fast lookups when you don't need fresh data.
        """
        return self._context_cache.get(user_id)
    
    def update_in_memory(self, user_id: int, context: ConversationContext) -> None:
        """
        Update in-memory context directly.
        
        Use this for transient updates (e.g., conversation history)
        that don't need immediate persistence.
        """
        self._context_cache[user_id] = context
        context.updated_at = datetime.utcnow()
    
    def is_context_stale(self, user_id: int, max_age_seconds: int = 60) -> bool:
        """
        Check if cached context might be stale.
        
        Args:
            user_id: User ID
            max_age_seconds: Maximum age before considering stale
            
        Returns:
            True if context is older than max_age_seconds or not cached
        """
        if user_id not in self._load_timestamps:
            return True
        
        age = datetime.utcnow() - self._load_timestamps[user_id]
        return age.total_seconds() > max_age_seconds


# Singleton instance
_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Get or create ContextManager singleton."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
