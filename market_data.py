from abc import ABC,abstractmethod
from collections import defaultdict,deque
from models import Candle
class MarketDataProvider(ABC):
 @abstractmethod
 async def candles(self,symbol,market,timeframe,limit=200):...
 @abstractmethod
 async def latest(self,symbol,market):...
class PaperMarketDataProvider(MarketDataProvider):
 def __init__(self):self.buffers=defaultdict(lambda:deque(maxlen=2000))
 def ingest(self,c):self.buffers[(c.market,c.symbol)].append(c)
 async def candles(self,symbol,market,timeframe,limit=200):return list(self.buffers[(market,symbol)])[-limit:]
 async def latest(self,symbol,market):
  b=self.buffers[(market,symbol)]; return b[-1] if b else None
 async def subscribe(self,symbols,market):return {"status":"paper","symbols":symbols,"market":market}
