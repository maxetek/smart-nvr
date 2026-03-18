import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import async_session
from app.redis_client import redis_client
from app.schemas.health import HealthResponse, DetailedHealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy", version=settings.app_version)


@router.get("/api/v1/health", response_model=DetailedHealthResponse)
async def detailed_health() -> DetailedHealthResponse:
    # Check database
    db_status = "connected"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        logger.warning("Database health check failed")

    # Check Redis
    redis_status = "connected"
    try:
        if not await redis_client.health_check():
            redis_status = "disconnected"
    except Exception:
        redis_status = "disconnected"
        logger.warning("Redis health check failed")

    return DetailedHealthResponse(
        status="healthy",
        database=db_status,
        redis=redis_status,
        version=settings.app_version,
    )
