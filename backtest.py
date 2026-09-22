from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable

import pandas as pd
import yfinance as yf

from ichimoku import calculate_ichimoku

NSE_INDEX_ALIASES = {"NIFTY 50": "^NSEI", "NIFTY50": "^NSEI", "BANKNIFTY": "^NSEBANK", "NIFTY BANK": "^NSEBANK", "SENSEX": "^BSESN"}

@dataclass
class BacktestTrade:
    symbol: str; side: str; entry_date: str; entry_price: float; exit_date: str; exit_price: float
    quantity: float; gross_pnl: float; costs: float; net_pnl: float; return_pct: float; exit_reason: str

def normalize_symbol(symbol: str, market: str) -> str:
    s = symbol.strip().upper()
    if market.upper() == "NSE":
        if s in NSE_INDEX_ALIASES: return NSE_INDEX_ALIASES[s]
        return s if "." in s or s.startswith("^") else f"{s}.NS"
    return s

def download_history(symbol: str, market: str, start: str, end: str, interval: str) -> pd.DataFrame:
    ticker = normalize_symbol(symbol, market)
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True,
                     progress=False, threads=False, multi_level_index=False)
    if df is None or df.empty: raise ValueError(f"No historical data returned for {symbol} ({ticker})")
    df = df.rename(columns=str.lower)
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Historical data missing columns: {', '.join(missing)}")
    df = df[required].dropna(subset=["open", "high", "low", "close"]).copy()
    if len(df) < 70: raise ValueError("Not enough candles; at least 70 are required for Ichimoku warm-up")
    return df

def _cost(notional: float, brokerage_pct: float, slippage_pct: float) -> float:
    return abs(notional) * (brokerage_pct + slippage_pct) / 100.0

def _drawdown(equity: pd.Series) -> float:
    if equity.empty: return 0.0
    peak = equity.cummax()
    return float(abs(((equity / peak) - 1).min()) * 100)

def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    x = calculate_ichimoku(df).copy()
    x["cross_up"] = (x.tenkan_sen.shift(1) <= x.kijun_sen.shift(1)) & (x.tenkan_sen > x.kijun_sen)
    x["cross_dn"] = (x.tenkan_sen.shift(1) >= x.kijun_sen.shift(1)) & (x.tenkan_sen < x.kijun_sen)
    x["cloud_bull"] = x.senkou_span_a > x.senkou_span_b
    x["cloud_bear"] = x.senkou_span_a < x.senkou_span_b
    x["cloud_top"] = x[["senkou_span_a", "senkou_span_b"]].max(axis=1)
    x["cloud_bottom"] = x[["senkou_span_a", "senkou_span_b"]].min(axis=1)
    x["buy_signal"] = x.cross_up & (x.close > x.cloud_top) & x.cloud_bull & x.chikou_confirm_bull
    x["short_signal"] = x.cross_dn & (x.close < x.cloud_bottom) & x.cloud_bear & x.chikou_confirm_bear
    x["exit_long"] = x.cross_dn & (x.close < x.cloud_bottom)
    x["exit_short"] = x.cross_up & (x.close > x.cloud_top)
    return x.dropna(subset=["tenkan_sen", "kijun_sen", "senkou_span_a", "senkou_span_b"])

def run_single_backtest(df, symbol, market, initial_capital, brokerage_pct, slippage_pct,
                        stop_pct, target_pct, allow_short):
    x = _prepare(df)
    cash = float(initial_capital); position = 0; qty = 0.0; entry_price = 0.0; entry_cost = 0.0; entry_date = None
    trades = []; curve = []

    def close_position(exit_price, date, reason):
        nonlocal cash, position, qty, entry_price, entry_cost, entry_date
        exit_cost = _cost(qty * exit_price, brokerage_pct, slippage_pct)
        gross = qty * (exit_price - entry_price) if position > 0 else qty * (entry_price - exit_price)
        total_cost = entry_cost + exit_cost
        net = gross - total_cost
        trades.append(asdict(BacktestTrade(symbol, "LONG" if position > 0 else "SHORT",
            str(entry_date), entry_price, str(date), exit_price, qty, gross, total_cost, net,
            net / max(entry_price * qty, 1e-9) * 100, reason)))
        if position > 0: cash += qty * exit_price - exit_cost
        else: cash -= qty * exit_price + exit_cost
        position = 0; qty = 0.0; entry_price = 0.0; entry_cost = 0.0; entry_date = None

    for i in range(1, len(x)):
        row = x.iloc[i]; prev = x.iloc[i - 1]; date = x.index[i]
        op, hi, lo, cl = map(float, [row.open, row.high, row.low, row.close])

        if position:
            stop = entry_price * (1 - stop_pct / 100) if position > 0 else entry_price * (1 + stop_pct / 100)
            target = entry_price * (1 + target_pct / 100) if position > 0 else entry_price * (1 - target_pct / 100)
            if position > 0:
                if lo <= stop: close_position(stop, date, "STOP")
                elif hi >= target: close_position(target, date, "TARGET")
                elif bool(prev.exit_long): close_position(op, date, "SIGNAL")
            else:
                if hi >= stop: close_position(stop, date, "STOP")
                elif lo <= target: close_position(target, date, "TARGET")
                elif bool(prev.exit_short): close_position(op, date, "SIGNAL")

        if not position and i >= 1 and op > 0:
            long_entry = bool(prev.buy_signal)
            short_entry = bool(prev.short_signal) and allow_short
            if long_entry or short_entry:
                # 100% of allocated capital, unlevered.
                qty = math.floor((cash / (op * (1 + (brokerage_pct + slippage_pct) / 100))) * 1_000_000) / 1_000_000
                if qty > 0:
                    entry_price = op; entry_cost = _cost(qty * op, brokerage_pct, slippage_pct); entry_date = date
                    if long_entry:
                        cash -= qty * op + entry_cost; position = 1
                    else:
                        cash += qty * op - entry_cost; position = -1

        marked = cash + (qty * cl if position > 0 else (-qty * cl if position < 0 else 0))
        curve.append({"date": str(date), "equity": float(marked)})

    if position:
        close_position(float(x.iloc[-1].close), x.index[-1], "END")
    final_equity = cash
    pnls = [t["net_pnl"] for t in trades]
    gross_profit = sum(max(0, t["gross_pnl"]) for t in trades)
    gross_loss = sum(max(0, -t["gross_pnl"]) for t in trades)
    wins = sum(p > 0 for p in pnls); losses = sum(p <= 0 for p in pnls)
    years = max((pd.Timestamp(df.index[-1]) - pd.Timestamp(df.index[0])).days / 365.25, 0)
    annualized = ((final_equity / initial_capital) ** (1 / years) - 1) * 100 if years and final_equity > 0 else None
    eq = pd.Series([p["equity"] for p in curve])
    return {
        "symbol": symbol, "market": market, "initial_capital": initial_capital, "final_equity": final_equity,
        "net_profit": final_equity - initial_capital, "return_pct": (final_equity / initial_capital - 1) * 100,
        "max_drawdown_pct": _drawdown(eq), "total_trades": len(trades), "winning_trades": wins,
        "losing_trades": losses, "win_rate_pct": wins / len(trades) * 100 if trades else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else None, "gross_profit": gross_profit,
        "gross_loss": gross_loss, "total_costs": sum(t["costs"] for t in trades),
        "annualized_return_pct": annualized, "trades": trades, "equity_curve": curve[-1000:]
    }

def run_backtest(symbols: Iterable[str], market: str, start: str, end: str, interval: str,
                 initial_capital: float, brokerage_pct: float, slippage_pct: float,
                 stop_pct: float = 2.0, target_pct: float = 4.0, allow_short: bool = False):
    symbols = [s.strip() for s in symbols if s.strip()]
    if not symbols: raise ValueError("At least one symbol is required")
    if len(symbols) > 102: raise ValueError("Maximum 102 symbols per backtest run")
    if initial_capital <= 0: raise ValueError("Initial capital must be positive")
    if brokerage_pct < 0 or slippage_pct < 0: raise ValueError("Brokerage and slippage cannot be negative")
    if stop_pct <= 0 or target_pct <= 0: raise ValueError("Stop-loss and target must be positive")
    allocation = initial_capital / len(symbols); results = []; errors = []
    for symbol in symbols:
        try:
            df = download_history(symbol, market, start, end, interval)
            results.append(run_single_backtest(df, symbol, market, allocation, brokerage_pct, slippage_pct,
                                               stop_pct, target_pct, allow_short))
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
    if not results: raise ValueError("; ".join(f"{e['symbol']}: {e['error']}" for e in errors) or "No backtests completed")
    final_equity = sum(r["final_equity"] for r in results)
    total_trades = sum(r["total_trades"] for r in results); wins = sum(r["winning_trades"] for r in results)
    gross_profit = sum(r["gross_profit"] for r in results); gross_loss = sum(r["gross_loss"] for r in results)
    return {
        "market": market, "symbols": symbols, "start": start, "end": end, "interval": interval,
        "initial_capital": initial_capital, "final_equity": final_equity, "net_profit": final_equity - initial_capital,
        "return_pct": (final_equity / initial_capital - 1) * 100, "max_drawdown_pct": max(r["max_drawdown_pct"] for r in results),
        "total_trades": total_trades, "winning_trades": wins, "losing_trades": total_trades - wins,
        "win_rate_pct": wins / total_trades * 100 if total_trades else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else None, "gross_profit": gross_profit,
        "gross_loss": gross_loss, "total_costs": sum(r["total_costs"] for r in results),
        "symbol_results": results, "errors": errors,
        "data_source": "Yahoo Finance via yfinance",
        "execution_model": "Signal at completed bar close; fill at next bar open; intrabar stop/target uses stop priority if both are touched."
    }
