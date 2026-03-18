import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session, engine
from app.middleware.rate_limit import RateLimitExceeded, _rate_limit_exceeded_handler, limiter
from app.pipeline.pipeline_manager import PipelineManager
from app.redis_client import redis_client
from app.routers import auth, cameras, dashboard, events, health, patterns, pipeline, users, ws

logger = logging.getLogger(__name__)


async def _create_initial_admin() -> None:
    """Create the initial admin user on first startup if no users exist."""
    from app.services.user_service import count_users, create_user

    async with async_session() as db:
        try:
            total = await count_users(db)
            if total == 0:
                await create_user(
                    db,
                    username=settings.initial_admin_username,
                    email=settings.initial_admin_email,
                    password=settings.initial_admin_password,
                    role="admin",
                )
                await db.commit()
                logger.info(
                    "Created initial admin user: %s", settings.initial_admin_username
                )
        except Exception:
            await db.rollback()
            logger.exception("Failed to create initial admin user")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    logging.basicConfig(level=settings.log_level)
    await redis_client.connect()

    # Create initial admin user
    await _create_initial_admin()

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

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(patterns.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(pipeline.router)
app.include_router(ws.router)
