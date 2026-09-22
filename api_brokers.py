from __future__ import annotations

from typing import Any
import httpx


class APIError(RuntimeError):
    pass


class AlpacaAdapter:
    """Alpaca Trading + Market Data REST adapter for US equities."""

    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self.trading_base = (
            "https://paper-api.alpaca.markets/v2"
            if paper else "https://api.alpaca.markets/v2"
        )
        self.data_base = "https://data.alpaca.markets/v2"

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise APIError("Alpaca API credentials are not configured")
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Accept": "application/json",
        }

    async def account(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.trading_base}/account", headers=self._headers())
            if r.status_code >= 400:
                raise APIError(f"Alpaca account error {r.status_code}: {r.text[:500]}")
            return r.json()

    async def positions(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.trading_base}/positions", headers=self._headers())
            if r.status_code >= 400:
                raise APIError(f"Alpaca positions error {r.status_code}: {r.text[:500]}")
            return r.json()

    async def latest(self, symbol: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{self.data_base}/stocks/{symbol}/bars/latest",
                params={"feed": "iex"},
                headers=self._headers(),
            )
            if r.status_code >= 400:
                raise APIError(f"Alpaca latest-data error {r.status_code}: {r.text[:500]}")
            return r.json()

    async def bars(
        self,
        symbols: list[str],
        timeframe: str = "1Day",
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "symbols": ",".join(symbols),
            "timeframe": timeframe,
            "limit": min(max(limit, 1), 10000),
            "feed": "iex",
            "adjustment": "all",
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(
                f"{self.data_base}/stocks/bars",
                params=params,
                headers=self._headers(),
            )
            if r.status_code >= 400:
                raise APIError(f"Alpaca bars error {r.status_code}: {r.text[:500]}")
            return r.json()

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{self.trading_base}/orders",
                json=payload,
                headers=self._headers(),
            )
            if r.status_code >= 400:
                raise APIError(f"Alpaca order error {r.status_code}: {r.text[:500]}")
            return r.json()


class KiteAdapter:
    """Zerodha Kite Connect REST adapter for NSE.

    A Kite access token is normally created through the broker's login flow and
    is intentionally supplied to the server as a secret environment variable.
    """

    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.base = "https://api.kite.trade"

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.access_token)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise APIError("Kite API key/access token are not configured")
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self.api_key}:{self.access_token}",
            "Accept": "application/json",
        }

    async def quote(self, symbol: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(
                f"{self.base}/quote",
                params={"i": f"NSE:{symbol}"},
                headers=self._headers(),
            )
            if r.status_code >= 400:
                raise APIError(f"Kite quote error {r.status_code}: {r.text[:500]}")
            data = r.json()
            if data.get("status") != "success":
                raise APIError(str(data))
            return data["data"]

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        product: str = "CNC",
        order_type: str = "MARKET",
        price: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tradingsymbol": symbol,
            "exchange": "NSE",
            "transaction_type": side.upper(),
            "quantity": int(quantity),
            "product": product,
            "order_type": order_type.upper(),
            "validity": "DAY",
        }
        if price is not None:
            payload["price"] = price
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{self.base}/orders/regular",
                data=payload,
                headers=self._headers(),
            )
            if r.status_code >= 400:
                raise APIError(f"Kite order error {r.status_code}: {r.text[:500]}")
            data = r.json()
            if data.get("status") != "success":
                raise APIError(str(data))
            return data["data"]

    async def orders(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.base}/orders", headers=self._headers())
            if r.status_code >= 400:
                raise APIError(f"Kite orders error {r.status_code}: {r.text[:500]}")
            data = r.json()
            if data.get("status") != "success":
                raise APIError(str(data))
            return data["data"]

    async def positions(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.base}/portfolio/positions", headers=self._headers())
            if r.status_code >= 400:
                raise APIError(f"Kite positions error {r.status_code}: {r.text[:500]}")
            data = r.json()
            if data.get("status") != "success":
                raise APIError(str(data))
            return data["data"]
