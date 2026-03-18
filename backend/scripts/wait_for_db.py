"""Wait for the database to be ready before starting the application."""

import asyncio
import logging
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)


async def wait_for_db(max_retries: int = 30, delay: float = 2.0) -> bool:
    engine = create_async_engine(settings.database_url)
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database is ready (attempt %d)", attempt)
            await engine.dispose()
            return True
        except Exception as e:
            logger.warning("Database not ready (attempt %d/%d): %s", attempt, max_retries, e)
            if attempt < max_retries:
                await asyncio.sleep(delay)
    await engine.dispose()
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not asyncio.run(wait_for_db()):
        logger.error("Database did not become ready in time")
        sys.exit(1)
