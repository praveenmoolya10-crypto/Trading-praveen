from abc import ABC,abstractmethod
from dataclasses import asdict
from models import Order
import uuid

class BrokerAdapter(ABC):
 @abstractmethod
 async def place_order(self,*args,**kwargs):...
 @abstractmethod
 async def cancel_order(self,order_id):...
 @abstractmethod
 async def positions(self):...
 @abstractmethod
 async def account(self):...

class PaperBroker(BrokerAdapter):
 def __init__(self,starting_cash=100000): self.orders={}; self._positions={}; self.cash=starting_cash; self.starting_cash=starting_cash
 async def place_order(self,symbol,market,side,quantity,order_type="MARKET",price=None):
  px=float(price or 0); oid=str(uuid.uuid4()); q=float(quantity); s=side.upper()
  if px<=0:return {"id":oid,"status":"REJECTED","error":"Paper broker requires a reference price"}
  pos=self._positions.get((market,symbol),{"quantity":0.0,"average_price":0.0})
  signed=q if s=="BUY" else -q; newq=pos["quantity"]+signed
  if s=="BUY": self.cash-=q*px
  else:self.cash+=q*px
  if newq==0:self._positions.pop((market,symbol),None)
  else:
   avg=px if pos["quantity"]==0 or (pos["quantity"]>0 and s=="SELL") else (pos["average_price"]*pos["quantity"]+q*px)/newq
   self._positions[(market,symbol)]={"quantity":newq,"average_price":avg}
  o=Order(oid,symbol,market,s,q,order_type,"FILLED",q,px,None)
  self.orders[oid]=o; return asdict(o)
 async def cancel_order(self,order_id):
  if order_id not in self.orders:return {"order_id":order_id,"status":"NOT_FOUND"}
  return {"order_id":order_id,"status":"CANCELLED"}
 async def positions(self):return [{"symbol":s,"market":m,**p} for (m,s),p in self._positions.items()]
 async def account(self):return {"cash":self.cash,"equity":self.cash,"mode":"paper"}
