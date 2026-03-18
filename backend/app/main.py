import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.redis_client import redis_client
from app.routers import health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    logging.basicConfig(level=settings.log_level)
    await redis_client.connect()
    logger.info("Smart NVR started — version %s", settings.app_version)
    yield
    # Shutdown
    await redis_client.disconnect()
    await engine.dispose()
    logger.info("Smart NVR shut down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent Network Video Recorder with AI-powered analytics",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
