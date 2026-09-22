from dataclasses import dataclass
import pandas as pd
from ichimoku import calculate_ichimoku

@dataclass
class Signal:
    signal:str; reason:str; stop_loss:float|None=None; target:float|None=None

def signal_for(df, stop_pct=.02, target_pct=.04):
    if len(df)<60: return Signal("HOLD","Need at least 60 candles")
    x=calculate_ichimoku(df).dropna()
    if len(x)<2: return Signal("HOLD","Ichimoku data not ready")
    r,p=x.iloc[-1],x.iloc[-2]
    top=max(r.senkou_span_a,r.senkou_span_b); bottom=min(r.senkou_span_a,r.senkou_span_b)
    cross_up=p.tenkan_sen<=p.kijun_sen and r.tenkan_sen>r.kijun_sen
    cross_dn=p.tenkan_sen>=p.kijun_sen and r.tenkan_sen<r.kijun_sen
    cloud_bull=r.senkou_span_a>r.senkou_span_b; cloud_bear=r.senkou_span_a<r.senkou_span_b
    # Chikou at the current bar must clear the price 26 bars back.
    chikou_bull=bool(r.chikou_confirm_bull); chikou_bear=bool(r.chikou_confirm_bear)
    if cross_up and r.close>top and cloud_bull and chikou_bull:
        return Signal("BUY","Tenkan>Kijun + price above bullish Kumo + Chikou confirmation",r.close*(1-stop_pct),r.close*(1+target_pct))
    if cross_dn and r.close<bottom and cloud_bear and chikou_bear:
        return Signal("SELL","Tenkan<Kijun + price below bearish Kumo + Chikou confirmation",r.close*(1+stop_pct),r.close*(1-target_pct))
    if cross_dn and r.close<bottom: return Signal("EXIT_LONG","Bearish cross and close below Kumo")
    if cross_up and r.close>top: return Signal("EXIT_SHORT","Bullish cross and close above Kumo")
    return Signal("HOLD","No complete Ichimoku condition")
