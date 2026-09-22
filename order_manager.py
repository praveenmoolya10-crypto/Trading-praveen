from database import execute,log_event
from datetime import datetime,timezone
class OrderManager:
 def __init__(self,broker,risk):self.broker=broker;self.risk=risk
 async def submit(self,symbol,market,side,qty,price):
  ok,reason=self.risk.validate(price,qty,side)
  if not ok: await log_event("WARN","ORDER_BLOCKED",{"symbol":symbol,"reason":reason}); return {"status":"REJECTED","error":reason}
  result=await self.broker.place_order(symbol,market,side,qty,price=price)
  now=datetime.now(timezone.utc).isoformat(); oid=result.get("id","")
  await execute("INSERT OR REPLACE INTO orders(id,symbol,market,side,quantity,order_type,status,filled_quantity,average_price,created_at,updated_at,error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(oid,symbol,market,side,qty,"MARKET",result.get("status"),result.get("filled_quantity",0),result.get("average_price"),now,now,result.get("error")))
  await log_event("INFO","ORDER_RESULT",result); return result
