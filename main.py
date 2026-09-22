from datetime import datetime
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from config import settings
from risk import RiskManager
from market_data import PaperMarketDataProvider
from broker import PaperBroker
from api_brokers import APIError, AlpacaAdapter, KiteAdapter
from ichimoku import generate_signal
from models import Candle
from backtest import run_backtest

app=FastAPI(title=settings.app_name,version="0.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
market_data=PaperMarketDataProvider()
broker=PaperBroker(settings.starting_cash)
alpaca=AlpacaAdapter(settings.nasdaq_api_key, settings.nasdaq_api_secret, settings.alpaca_paper)
kite=KiteAdapter(settings.nse_api_key, settings.nse_access_token)
risk=RiskManager(settings.max_daily_loss,settings.max_open_positions,settings.max_order_value,settings.risk_per_trade)
auto_trading=False

class CandleIn(BaseModel):
    symbol:str; market:str; timestamp:str; open:float; high:float; low:float; close:float; volume:float=0
class OrderIn(BaseModel):
    symbol:str; market:str; side:str; quantity:float; price:float=0

class BacktestIn(BaseModel):
    market:str = "NSE"
    symbols:list[str] = ["RELIANCE"]
    start:str = "2020-01-01"
    end:str = "2026-01-01"
    interval:str = "1d"
    initial_capital:float = 100000
    brokerage_pct:float = 0.03
    slippage_pct:float = 0.05
    stop_pct:float = 2.0
    target_pct:float = 4.0
    allow_short:bool = False

@app.get("/api/health")
async def health():
    return {"status":"ok","environment":settings.environment,"live_trading_enabled":settings.live_trading_enabled,"auto_trading":auto_trading,"emergency_stop":risk.emergency_stop,"providers":{"NSE":{"broker":"kite","configured":kite.configured},"NASDAQ":{"broker":"alpaca","configured":alpaca.configured,"paper":settings.alpaca_paper}}}

@app.post("/api/control/start")
async def start():
    global auto_trading
    if risk.emergency_stop: raise HTTPException(409,"Emergency stop is active")
    if settings.environment!="paper" and not settings.live_trading_enabled: raise HTTPException(409,"Live trading is disabled")
    auto_trading=True
    return {"auto_trading":True}

@app.post("/api/control/stop")
async def stop():
    global auto_trading
    auto_trading=False
    return {"auto_trading":False}

@app.post("/api/control/emergency-stop")
async def emergency():
    global auto_trading
    auto_trading=False; risk.emergency_stop=True
    return {"auto_trading":False,"emergency_stop":True}

@app.post("/api/control/emergency-reset")
async def reset_emergency():
    risk.emergency_stop=False
    return {"emergency_stop":False}

@app.get("/api/providers")
async def providers():
    return {
        "NSE": {"broker": "kite", "configured": kite.configured},
        "NASDAQ": {"broker": "alpaca", "configured": alpaca.configured, "paper": settings.alpaca_paper},
        "live_trading_enabled": settings.live_trading_enabled,
    }

@app.get("/api/market/latest/{market}/{symbol}")
async def api_latest(market: str, symbol: str):
    market = market.upper()
    try:
        if market == "NASDAQ":
            return {"market": market, "symbol": symbol.upper(), "source": "alpaca", "data": await alpaca.latest(symbol.upper())}
        if market == "NSE":
            return {"market": market, "symbol": symbol.upper(), "source": "kite", "data": await kite.quote(symbol.upper())}
        raise HTTPException(400, "Market must be NSE or NASDAQ")
    except APIError as exc:
        raise HTTPException(502, str(exc))

@app.post("/api/market/candle")
async def candle(c:CandleIn):
    market_data.ingest(Candle(c.symbol,c.market,datetime.fromisoformat(c.timestamp),c.open,c.high,c.low,c.close,c.volume))
    return {"status":"accepted"}

@app.get("/api/signal/{market}/{symbol}")
async def signal(market:str,symbol:str):
    candles=await market_data.candles(symbol,market,"1m",500)
    if not candles: return {"signal":"HOLD","reason":"No market data"}
    df=pd.DataFrame([vars(x) for x in candles])
    return generate_signal(df,settings.default_stop_loss_pct,settings.default_target_pct).__dict__

@app.post("/api/orders")
async def order(o:OrderIn):
    ok,reason=risk.validate(o.price,o.quantity,o.side)
    if not ok: raise HTTPException(400,reason)
    market=o.market.upper()
    if market == "NASDAQ" and alpaca.configured:
        if not settings.live_trading_enabled and not settings.alpaca_paper:
            raise HTTPException(409,"Live Alpaca trading is disabled")
        try:
            return await alpaca.place_order(o.symbol.upper(),o.side,o.quantity)
        except APIError as exc:
            raise HTTPException(502,str(exc))
    if market == "NSE" and kite.configured and settings.live_trading_enabled:
        try:
            return await kite.place_order(o.symbol.upper(),o.side,o.quantity)
        except APIError as exc:
            raise HTTPException(502,str(exc))
    # NSE uses the local paper broker whenever live trading is disabled.
    # Kite can still provide market data without placing real orders.
    return await broker.place_order(o.symbol,o.market,o.side,o.quantity,price=o.price)

@app.post("/api/backtest")
async def backtest(req:BacktestIn):
    if req.market.upper() not in {"NSE", "NASDAQ"}: raise HTTPException(400,"Market must be NSE or NASDAQ")
    if req.interval not in {"1d","1wk","1mo","1h","60m","30m","15m","5m","1m"}: raise HTTPException(400,"Unsupported timeframe")
    try:
        return run_backtest(req.symbols,req.market.upper(),req.start,req.end,req.interval,req.initial_capital,req.brokerage_pct,req.slippage_pct,req.stop_pct,req.target_pct,req.allow_short)
    except Exception as exc:
        raise HTTPException(400,str(exc))

@app.get("/api/positions")
async def positions():
    try:
        result=[]
        if alpaca.configured:
            result.extend(await alpaca.positions())
        if kite.configured:
            k=await kite.positions()
            result.extend(k.get("net", []))
        if result:
            return result
    except APIError as exc:
        raise HTTPException(502,str(exc))
    return await broker.positions()

@app.get("/api/account")
async def account():
    try:
        if alpaca.configured:
            return await alpaca.account()
    except APIError as exc:
        raise HTTPException(502,str(exc))
    return await broker.account()

dist=Path(__file__).parent/"dist"
if dist.exists():
    app.mount("/assets",StaticFiles(directory=dist/"assets"),name="assets")
    @app.get("/{path:path}")
    async def dashboard(path:str):
        requested=dist/path
        if path and requested.is_file(): return FileResponse(requested)
        return FileResponse(dist/"index.html")
