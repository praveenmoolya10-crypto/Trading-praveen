from abc import ABC, abstractmethod
from dataclasses import asdict
import uuid
from app.data.models import Order

class BrokerAdapter(ABC):
    @abstractmethod
    async def place_order(self, symbol, side, quantity, order_type="MARKET", price=None): ...
    @abstractmethod
    async def cancel_order(self, order_id): ...
    @abstractmethod
    async def positions(self): ...
    @abstractmethod
    async def account(self): ...

class PaperBroker(BrokerAdapter):
    def __init__(self): self.orders={}; self._positions={}; self.cash=100000.0
    async def place_order(self, symbol, side, quantity, order_type="MARKET", price=None):
        oid=str(uuid.uuid4()); px=price or 0
        o=Order(oid,symbol,side,quantity,order_type,"FILLED",quantity,px)
        self.orders[oid]=o
        return asdict(o)
    async def cancel_order(self, order_id):
        if order_id in self.orders: self.orders[order_id].status="CANCELLED"
        return {"order_id":order_id,"status":"CANCELLED"}
    async def positions(self): return self._positions
    async def account(self): return {"cash":self.cash,"mode":"paper"}
