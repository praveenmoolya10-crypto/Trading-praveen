from dataclasses import dataclass
import pandas as pd

@dataclass
class IchimokuSignal:
    signal: str
    reason: str
    stop_loss: float | None = None
    target: float | None = None

def calculate_ichimoku(df: pd.DataFrame, tenkan=9, kijun=26, senkou_b=52) -> pd.DataFrame:
    out = df.copy()
    high, low, close = out["high"], out["low"], out["close"]
    out["tenkan_sen"] = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    out["kijun_sen"] = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    out["senkou_span_a"] = ((out["tenkan_sen"] + out["kijun_sen"]) / 2).shift(kijun)
    out["senkou_span_b"] = ((high.rolling(senkou_b).max() + low.rolling(senkou_b).min()) / 2).shift(kijun)
    out["chikou_span"] = close.shift(-kijun)
    return out

def generate_signal(df: pd.DataFrame, stop_pct=.02, target_pct=.04) -> IchimokuSignal:
    x = calculate_ichimoku(df).dropna()
    if len(x) < 2:
        return IchimokuSignal("HOLD", "Not enough candles")
    r = x.iloc[-1]; p = x.iloc[-2]
    cloud_top = max(r.senkou_span_a, r.senkou_span_b)
    cloud_bottom = min(r.senkou_span_a, r.senkou_span_b)
    bullish_cross = p.tenkan_sen <= p.kijun_sen and r.tenkan_sen > r.kijun_sen
    bearish_cross = p.tenkan_sen >= p.kijun_sen and r.tenkan_sen < r.kijun_sen
    above_cloud = r.close > cloud_top
    below_cloud = r.close < cloud_bottom
    chikou_bull = r.chikou_span > x.iloc[-1].close if pd.notna(r.chikou_span) else False
    chikou_bear = r.chikou_span < x.iloc[-1].close if pd.notna(r.chikou_span) else False
    if bullish_cross and above_cloud:
        return IchimokuSignal("BUY", "Bullish Tenkan/Kijun cross above cloud", r.close*(1-stop_pct), r.close*(1+target_pct))
    if bearish_cross and below_cloud:
        return IchimokuSignal("SELL", "Bearish Tenkan/Kijun cross below cloud", r.close*(1+stop_pct), r.close*(1-target_pct))
    if below_cloud and bearish_cross:
        return IchimokuSignal("EXIT_LONG", "Bearish reversal below cloud")
    if above_cloud and bullish_cross:
        return IchimokuSignal("EXIT_SHORT", "Bullish reversal above cloud")
    return IchimokuSignal("HOLD", "No confirmed Ichimoku entry/exit condition")
