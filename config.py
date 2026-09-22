from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Ichimoku Multi-Market Auto Trader"
    environment: str = "paper"
    database_url: str = "sqlite+aiosqlite:///./trader.db"
    host: str = "0.0.0.0"
    port: int = 8000

    ichimoku_tenkan: int = 9
    ichimoku_kijun: int = 26
    ichimoku_senkou_b: int = 52

    max_daily_loss: float = 1000
    max_open_positions: int = 10
    max_order_value: float = 10000
    risk_per_trade: float = 0.01
    default_stop_loss_pct: float = 0.02
    default_target_pct: float = 0.04
    starting_cash: float = 100000

    # API providers. Keep secrets out of GitHub and the frontend.
    nse_broker: str = "kite"
    nse_api_key: str = ""
    nse_access_token: str = ""
    nasdaq_broker: str = "alpaca"
    nasdaq_api_key: str = ""
    nasdaq_api_secret: str = ""
    alpaca_paper: bool = True

    # Hard safety switch. Must be explicitly enabled server-side for live orders.
    live_trading_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
