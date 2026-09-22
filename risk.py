from dataclasses import dataclass

@dataclass
class RiskManager:
    max_daily_loss: float
    max_open_positions: int
    risk_per_trade: float
    max_order_value: float
    daily_pnl: float = 0.0
    open_positions: int = 0
    emergency_stop: bool = False

    def validate(self, price: float, quantity: float) -> tuple[bool,str]:
        if self.emergency_stop: return False, "Emergency stop active"
        if self.daily_pnl <= -abs(self.max_daily_loss): return False, "Maximum daily loss reached"
        if self.open_positions >= self.max_open_positions: return False, "Maximum open positions reached"
        if price * quantity > self.max_order_value: return False, "Maximum order value exceeded"
        if quantity <= 0 or price <= 0: return False, "Invalid price or quantity"
        return True, "OK"
