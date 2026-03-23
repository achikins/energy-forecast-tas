"""
FastAPI application factory.

Registers routers, configures CORS, fetches live AEMO data on startup,
and schedules an hourly background refresh so the cache stays current.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import historical, forecast, insights, decision
from app.services.data_service import refresh_data, cache_age_seconds, CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


async def _background_refresh():
    """Periodically refresh the AEMO data cache every CACHE_TTL_SECONDS."""
    while True:
        await asyncio.sleep(CACHE_TTL_SECONDS)
        try:
            await asyncio.to_thread(refresh_data)
        except Exception as e:
            logger.error("Background data refresh failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initial data load at startup (blocking so first request is never cold)
    try:
        await asyncio.to_thread(refresh_data)
    except Exception as e:
        logger.error("Startup data load failed: %s", e)

    # Launch hourly background refresh
    task = asyncio.create_task(_background_refresh())

    yield

    task.cancel()


app = FastAPI(
    title="Energy Demand Forecasting API",
    description="Historical demand retrieval, short-term forecasting, and demand analytics for Tasmania.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(historical.router, prefix=API_PREFIX)
app.include_router(forecast.router, prefix=API_PREFIX)
app.include_router(insights.router, prefix=API_PREFIX)
app.include_router(decision.router, prefix=API_PREFIX)


@app.get("/health", tags=["meta"])
def health_check():
    """Liveness probe — confirms the service is running and reports cache age."""
    age = cache_age_seconds()
    return {
        "status": "ok",
        "version": "1.0.0",
        "data_cache_age_seconds": round(age) if age is not None else None,
    }
