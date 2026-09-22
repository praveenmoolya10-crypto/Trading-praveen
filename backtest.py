import pandas as pd
from strategy_engine import signal_for

def run_backtest(df,initial_cash=100000,stop_pct=.02,target_pct=.04):
 cash=float(initial_cash); qty=0; entry=0; trades=[]
 for i in range(60,len(df)):
  window=df.iloc[:i+1]; s=signal_for(window,stop_pct,target_pct); px=float(window.iloc[-1].close)
  if qty==0 and s.signal=="BUY": qty=int(cash/px); entry=px; cash-=qty*px
  elif qty>0 and s.signal in ("SELL","EXIT_LONG"):
   pnl=(px-entry)*qty; cash+=qty*px; trades.append({"side":"EXIT","price":px,"qty":qty,"pnl":pnl}); qty=0
  elif qty>0 and px<=entry*(1-stop_pct):
   pnl=(px-entry)*qty; cash+=qty*px; trades.append({"side":"STOP","price":px,"qty":qty,"pnl":pnl}); qty=0
 equity=cash+qty*float(df.iloc[-1].close); pnls=[t["pnl"] for t in trades]
 return {"initial_cash":initial_cash,"final_equity":equity,"net_pnl":equity-initial_cash,"trades":len(trades),"wins":sum(p>0 for p in pnls),"losses":sum(p<=0 for p in pnls)}
