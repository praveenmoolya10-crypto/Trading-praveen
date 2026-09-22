from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class Candle:
    symbol: str
    market: Literal["NSE", "NASDAQ"]
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0

@dataclass
class Order:
    id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    status: str
    filled_quantity: float = 0
    average_price: float | None = None
