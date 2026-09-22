from dataclasses import dataclass
import pandas as pd
@dataclass
class IchimokuSignal:
 signal:str; reason:str; stop_loss:float|None=None; target:float|None=None

def calculate_ichimoku(df,tenkan=9,kijun=26,senkou_b=52):
 out=df.copy(); h,l,c=out.high,out.low,out.close
 out["tenkan_sen"]=(h.rolling(tenkan).max()+l.rolling(tenkan).min())/2
 out["kijun_sen"]=(h.rolling(kijun).max()+l.rolling(kijun).min())/2
 out["senkou_span_a"]=((out.tenkan_sen+out.kijun_sen)/2).shift(kijun)
 out["senkou_span_b"]=((h.rolling(senkou_b).max()+l.rolling(senkou_b).min())/2).shift(kijun)
 # Chikou value is current close plotted 26 periods back; confirmation compares it with price 26 bars ago.
 out["chikou_span"]=c
 out["chikou_confirm_bull"]=c>c.shift(kijun)
 out["chikou_confirm_bear"]=c<c.shift(kijun)
 return out

def generate_signal(df,stop_pct=.02,target_pct=.04):
 from strategy_engine import signal_for
 return signal_for(df,stop_pct,target_pct)
