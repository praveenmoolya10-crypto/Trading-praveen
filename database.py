import aiosqlite, json, os
from datetime import datetime, timezone
DB=os.getenv("DATABASE_PATH","trader.db")

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS candles(id INTEGER PRIMARY KEY,symbol TEXT,market TEXT,timeframe TEXT,timestamp TEXT,open REAL,high REAL,low REAL,close REAL,volume REAL);
        CREATE INDEX IF NOT EXISTS idx_candles ON candles(market,symbol,timeframe,timestamp);
        CREATE TABLE IF NOT EXISTS signals(id INTEGER PRIMARY KEY,symbol TEXT,market TEXT,timestamp TEXT,signal TEXT,reason TEXT,price REAL,stop_loss REAL,target REAL);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,symbol TEXT,market TEXT,side TEXT,quantity REAL,order_type TEXT,status TEXT,filled_quantity REAL,average_price REAL,created_at TEXT,updated_at TEXT,broker_order_id TEXT,error TEXT);
        CREATE TABLE IF NOT EXISTS positions(symbol TEXT,market TEXT PRIMARY KEY,quantity REAL,average_price REAL,unrealized_pnl REAL,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT,symbol TEXT,market TEXT,side TEXT,quantity REAL,price REAL,pnl REAL,timestamp TEXT,order_id TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,level TEXT,event TEXT,payload TEXT,timestamp TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        """); await db.commit()

async def execute(sql, params=(), fetch=False):
    async with aiosqlite.connect(DB) as db:
        cur=await db.execute(sql,params)
        rows=await cur.fetchall() if fetch else []
        await db.commit(); return rows

async def log_event(level,event,payload=None):
    await execute("INSERT INTO events(level,event,payload,timestamp) VALUES(?,?,?,?)",(level,event,json.dumps(payload or {}),datetime.now(timezone.utc).isoformat()))
