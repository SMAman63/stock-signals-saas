import json
from typing import Any, Optional
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()


class RedisService:
    """Redis service for caching and rate limiting."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set a value in Redis with optional TTL."""
        if not self.redis:
            return False
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        if not self.redis:
            return False
        return await self.redis.exists(key) > 0
    
    async def incr(self, key: str) -> int:
        """Increment a counter in Redis."""
        if not self.redis:
            return 0
        return await self.redis.incr(key)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on a key."""
        if not self.redis:
            return False
        return await self.redis.expire(key, ttl)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get and parse JSON from Redis."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set_json(self, key: str, value: Any, ttl: int = None) -> bool:
        """Serialize and store JSON in Redis."""
        return await self.set(key, json.dumps(value), ttl)


# Global Redis service instance
redis_service = RedisService()


async def get_redis() -> RedisService:
    """Dependency to get Redis service."""
    return redis_service
