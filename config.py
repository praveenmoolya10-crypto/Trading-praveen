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
    risk_per_trade: float = 0.01
    default_stop_loss_pct: float = 0.02
    default_target_pct: float = 0.04
    max_order_value: float = 10000
    nse_broker: str = "paper"
    nse_api_key: str = ""
    nse_api_secret: str = ""
    nasdaq_broker: str = "paper"
    nasdaq_api_key: str = ""
    nasdaq_api_secret: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
