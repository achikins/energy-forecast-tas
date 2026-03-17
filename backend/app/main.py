"""
FastAPI application factory.

Registers routers, configures CORS, and pre-warms the data cache
on startup so the first request doesn't incur a cold-load delay.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import historical, forecast, insights
from app.services.data_service import get_dataframe


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load dataset into memory on startup."""
    try:
        df = get_dataframe()
        print(f"[startup] Dataset loaded: {len(df):,} records")
    except FileNotFoundError as e:
        print(f"[startup] WARNING: {e}")
    yield
    # Nothing to clean up — lru_cache holds the DataFrame for the process lifetime


app = FastAPI(
    title="Energy Demand Forecasting API",
    description="Historical demand retrieval, short-term forecasting, and demand analytics for Tasmania.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow the Vite dev server and any configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Register API routers under /api/v1 prefix
API_PREFIX = "/api/v1"
app.include_router(historical.router, prefix=API_PREFIX)
app.include_router(forecast.router, prefix=API_PREFIX)
app.include_router(insights.router, prefix=API_PREFIX)


@app.get("/health", tags=["meta"])
def health_check():
    """Liveness probe — confirms the service is running."""
    return {"status": "ok", "version": "1.0.0"}
