import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.pipeline.pipeline_manager import PipelineManager
from app.redis_client import redis_client
from app.routers import health, pipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    logging.basicConfig(level=settings.log_level)
    await redis_client.connect()

    # Initialize pipeline manager
    manager = PipelineManager()
    await manager.initialize()
    await manager.start_consumer()
    app.state.pipeline_manager = manager

    logger.info("Smart NVR started — version %s", settings.app_version)
    yield
    # Shutdown
    await manager.shutdown()
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
app.include_router(pipeline.router)
