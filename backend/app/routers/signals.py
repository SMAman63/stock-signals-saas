from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.signals import Signal, SignalsResponse
from app.services.auth import get_current_user
from app.services.redis_service import RedisService, get_redis

router = APIRouter(prefix="/signals", tags=["Signals"])

# Mock signals data (simulating Zerodha-like data)
MOCK_SIGNALS = [
    {
        "symbol": "NIFTY",
        "action": "BUY",
        "price": 22450.50,
        "target": 22650.00,
        "stop_loss": 22350.00,
        "timestamp": "2024-01-28T10:30:00Z"
    },
    {
        "symbol": "BANKNIFTY",
        "action": "SELL",
        "price": 48200.00,
        "target": 47800.00,
        "stop_loss": 48400.00,
        "timestamp": "2024-01-28T10:35:00Z"
    },
    {
        "symbol": "RELIANCE",
        "action": "BUY",
        "price": 2890.25,
        "target": 2950.00,
        "stop_loss": 2860.00,
        "timestamp": "2024-01-28T10:40:00Z"
    },
    {
        "symbol": "TCS",
        "action": "HOLD",
        "price": 4125.00,
        "target": 4200.00,
        "stop_loss": 4050.00,
        "timestamp": "2024-01-28T10:45:00Z"
    },
    {
        "symbol": "HDFC BANK",
        "action": "BUY",
        "price": 1650.75,
        "target": 1720.00,
        "stop_loss": 1620.00,
        "timestamp": "2024-01-28T10:50:00Z"
    },
    {
        "symbol": "INFOSYS",
        "action": "SELL",
        "price": 1580.00,
        "target": 1520.00,
        "stop_loss": 1610.00,
        "timestamp": "2024-01-28T10:55:00Z"
    },
    {
        "symbol": "ICICI BANK",
        "action": "BUY",
        "price": 1120.50,
        "target": 1180.00,
        "stop_loss": 1090.00,
        "timestamp": "2024-01-28T11:00:00Z"
    },
    {
        "symbol": "SBIN",
        "action": "BUY",
        "price": 780.25,
        "target": 820.00,
        "stop_loss": 760.00,
        "timestamp": "2024-01-28T11:05:00Z"
    },
]

# Cache key and TTL
SIGNALS_CACHE_KEY = "signals:all"
SIGNALS_CACHE_TTL = 300  # 5 minutes

# Free users see limited signals
FREE_USER_SIGNAL_LIMIT = 3


async def get_signals_data(redis: RedisService) -> list[dict]:
    """Get signals data, using cache if available."""
    # Try to get from cache
    cached = await redis.get_json(SIGNALS_CACHE_KEY)
    if cached:
        return cached
    
    # Simulate fetching from external API (e.g., Zerodha)
    # In production, this would make an actual API call
    signals = MOCK_SIGNALS.copy()
    
    # Update timestamps to current time for freshness
    current_time = datetime.utcnow().isoformat() + "Z"
    for signal in signals:
        signal["timestamp"] = current_time
    
    # Cache the signals
    await redis.set_json(SIGNALS_CACHE_KEY, signals, ttl=SIGNALS_CACHE_TTL)
    
    return signals


@router.get("", response_model=SignalsResponse)
async def get_signals(
    current_user: Annotated[User, Depends(get_current_user)],
    redis: Annotated[RedisService, Depends(get_redis)],
):
    """
    Get stock signals.
    
    - Paid users: See all signals
    - Free users: See limited signals (first 3)
    """
    all_signals = await get_signals_data(redis)
    total_count = len(all_signals)
    
    # Filter based on subscription status
    if current_user.is_paid:
        signals = all_signals
        is_limited = False
    else:
        signals = all_signals[:FREE_USER_SIGNAL_LIMIT]
        is_limited = True
    
    # Convert to Signal objects
    signal_objects = [
        Signal(
            symbol=s["symbol"],
            action=s["action"],
            price=s["price"],
            target=s["target"],
            stop_loss=s["stop_loss"],
            timestamp=datetime.fromisoformat(s["timestamp"].replace("Z", "+00:00"))
        )
        for s in signals
    ]
    
    return SignalsResponse(
        signals=signal_objects,
        is_limited=is_limited,
        total_count=total_count
    )
