# Ichimoku Multi-Market Auto Trader

A production-oriented starter architecture for NSE + NASDAQ automated trading. It deliberately defaults to **paper mode**.

## Included
- React dashboard
- FastAPI backend
- Ichimoku calculation: Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span
- BUY / SELL / HOLD / EXIT signal engine
- Risk controls: max daily loss, max positions, max order value, stop-loss/target parameters
- Broker adapter interface + paper broker
- Market-data provider interface + paper candle ingestion
- Start / Stop / Emergency Stop controls
- Health/status API
- Docker Compose

## Required before real trading
1. Select a supported NSE broker and a supported US/Nasdaq broker/data provider.
2. Implement their authenticated REST/WebSocket adapters in `backend/app/execution/` and `backend/app/data/`.
3. Add PostgreSQL/Redis for production persistence/queues.
4. Add a durable order/state machine and reconciliation loop.
5. Add historical-data ingestion and the backtesting engine.
6. Add authentication, encrypted secrets, audit logs, alerting and monitoring.
7. Validate strategy/risk rules and broker/regulatory requirements before enabling live orders.

## Run
Copy `backend/.env.example` to `backend/.env`, then:

```bash
docker compose up --build
```

Dashboard: http://localhost:5173
API: http://localhost:8000/docs

## Important strategy note
The included signal engine is an explicit baseline, not a claim of profitability. It uses a bullish/bearish Tenkan/Kijun cross with cloud confirmation. Chikou is calculated but should be made part of the final confirmation rule if that is your chosen strategy definition.
