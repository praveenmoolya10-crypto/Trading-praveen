from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from app.core.config import settings
from app.core.risk import RiskManager
from app.data.market_data import PaperMarketDataProvider
from app.execution.broker import PaperBroker
from app.strategy.ichimoku import generate_signal

app = FastAPI(title=settings.app_name, version="0.1.0")
market_data=PaperMarketDataProvider(); broker=PaperBroker()
risk=RiskManager(settings.max_daily_loss,settings.max_open_positions,settings.risk_per_trade,settings.max_order_value)
auto_trading=False

class CandleIn(BaseModel):
    symbol:str; market:str; timestamp:str; open:float; high:float; low:float; close:float; volume:float=0
class OrderIn(BaseModel):
    symbol:str; side:str; quantity:float; price:float=0

@app.get("/api/health")
async def health(): return {"status":"ok","environment":settings.environment,"auto_trading":auto_trading,"emergency_stop":risk.emergency_stop}

@app.post("/api/control/start")
async def start():
    global auto_trading
    if risk.emergency_stop: raise HTTPException(409,"Emergency stop is active")
    auto_trading=True; return {"auto_trading":True}

@app.post("/api/control/stop")
async def stop():
    global auto_trading
    auto_trading=False; return {"auto_trading":False}

@app.post("/api/control/emergency-stop")
async def emergency():
    global auto_trading
    auto_trading=False; risk.emergency_stop=True; return {"auto_trading":False,"emergency_stop":True}

@app.post("/api/control/emergency-reset")
async def reset_emergency():
    risk.emergency_stop=False; return {"emergency_stop":False}

@app.post("/api/market/candle")
async def candle(c:CandleIn):
    from datetime import datetime
    from app.data.models import Candle
    market_data.ingest(Candle(c.symbol,c.market,datetime.fromisoformat(c.timestamp),c.open,c.high,c.low,c.close,c.volume))
    return {"status":"accepted"}

@app.get("/api/signal/{market}/{symbol}")
async def signal(market:str,symbol:str):
    candles=await market_data.candles(symbol,market,"1m",500)
    if not candles: return {"signal":"HOLD","reason":"No market data"}
    df=pd.DataFrame([vars(x) for x in candles])
    return generate_signal(df).__dict__

@app.post("/api/orders")
async def order(o:OrderIn):
    ok,reason=risk.validate(o.price,o.quantity)
    if not ok: raise HTTPException(400,reason)
    if not auto_trading and settings.environment != "paper": raise HTTPException(409,"Automated trading is stopped")
    return await broker.place_order(o.symbol,o.side,o.quantity,price=o.price)

@app.get("/api/positions")
async def positions(): return await broker.positions()

@app.get("/api/account")
async def account(): return await broker.account()
