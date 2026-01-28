from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class Signal(BaseModel):
    """Schema for a stock signal."""
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    price: float
    target: float
    stop_loss: float
    timestamp: datetime


class SignalsResponse(BaseModel):
    """Schema for signals response."""
    signals: list[Signal]
    is_limited: bool
    total_count: int
