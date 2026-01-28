from typing import Annotated
from fastapi import Request, HTTPException, status, Depends

from app.services.redis_service import RedisService, get_redis


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def check_rate_limit(
        self,
        request: Request,
        redis: Annotated[RedisService, Depends(get_redis)]
    ):
        """Check if the request is within rate limits."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        
        # Create rate limit key
        key = f"ratelimit:{endpoint}:{client_ip}"
        
        # Get current count
        current = await redis.incr(key)
        
        # Set expiry on first request
        if current == 1:
            await redis.expire(key, self.window_seconds)
        
        # Check if over limit
        if current > self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {self.window_seconds} seconds."
            )
        
        return True


# Create rate limiter instances
auth_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
