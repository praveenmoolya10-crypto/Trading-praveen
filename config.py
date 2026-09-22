from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Ichimoku Multi-Market Auto Trader"
    environment: str = "paper"
    database_url: str = "sqlite+aiosqlite:///./trader.db"
    host: str = "0.0.0.0"
    port: int = 8000

    # Ichimoku
    ichimoku_tenkan: int = 9
    ichimoku_kijun: int = 26
    ichimoku_senkou_b: int = 52

    # Risk
    max_daily_loss: float = 1000
    max_open_positions: int = 10
    max_order_value: float = 10000
    risk_per_trade: float = 0.01
    default_stop_loss_pct: float = 0.02
    default_target_pct: float = 0.04
    starting_cash: float = 100000

    # Leave these blank until you choose/configure your brokers.
    # Credentials must be supplied through the server-side .env/environment,
    # never committed to GitHub or placed in the frontend.
    nse_broker: str = ""
    nse_api_key: str = ""
    nse_api_secret: str = ""
    nasdaq_broker: str = ""
    nasdaq_api_key: str = ""
    nasdaq_api_secret: str = ""

    # Safety: live trading stays disabled unless explicitly enabled later.
    live_trading_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
