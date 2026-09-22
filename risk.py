from dataclasses import dataclass
@dataclass
class RiskManager:
    max_daily_loss:float; max_open_positions:int; max_order_value:float; risk_per_trade:float
    daily_pnl:float=0; open_positions:int=0; emergency_stop:bool=False
    def validate(self,price,quantity,side="BUY"):
        if self.emergency_stop:return False,"Emergency stop active"
        if price<=0 or quantity<=0:return False,"Invalid price or quantity"
        if self.daily_pnl<=-abs(self.max_daily_loss):return False,"Maximum daily loss reached"
        if side.upper() in ("BUY","SELL") and self.open_positions>=self.max_open_positions and side.upper()=="BUY":return False,"Maximum open positions reached"
        if price*quantity>self.max_order_value:return False,"Maximum order value exceeded"
        return True,"OK"
    def size_for_risk(self,entry,stop,equity):
        risk_cash=max(0,equity*self.risk_per_trade); distance=abs(entry-stop)
        return 0 if distance==0 else max(0,int(risk_cash/distance))
