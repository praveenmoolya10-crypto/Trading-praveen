from abc import ABC, abstractmethod
from collections import defaultdict, deque
from .models import Candle

class MarketDataProvider(ABC):
    @abstractmethod
    async def subscribe(self, symbols: list[str], market: str): ...
    @abstractmethod
    async def candles(self, symbol: str, market: str, timeframe: str, limit: int = 200): ...

class PaperMarketDataProvider(MarketDataProvider):
    def __init__(self): self.buffers = defaultdict(lambda: deque(maxlen=1000))
    async def subscribe(self, symbols, market): return {"status":"subscribed", "symbols":symbols, "market":market}
    async def candles(self, symbol, market, timeframe, limit=200):
        return list(self.buffers[(market, symbol)])[-limit:]
    def ingest(self, candle: Candle): self.buffers[(candle.market, candle.symbol)].append(candle)
