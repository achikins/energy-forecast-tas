"""
Application configuration loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Paths
    data_path: str = str(Path(__file__).parent.parent / "data" / "energy_demand.csv")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS — comma-separated list of allowed origins
    # In production, set CORS_ORIGINS to your Vercel deployment URL
    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://energy-forecast-tas.vercel.app"

    # Forecasting
    forecast_periods: int = 48  # default hours to forecast ahead

    class Config:
        env_file = ".env"


settings = Settings()
