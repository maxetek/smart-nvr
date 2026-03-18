from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, url: str = settings.redis_url) -> None:
        self._url = url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self._url, decode_responses=True)
        logger.info("Connected to Redis at %s", self._url)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not connected. Call connect() first.")
        return self._client

    async def health_check(self) -> bool:
        try:
            return await self.client.ping()
        except Exception:
            return False

    async def publish_event(self, stream_name: str, data: dict[str, Any]) -> str:
        """Publish an event to a Redis Stream using XADD."""
        payload = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()}
        message_id: str = await self.client.xadd(stream_name, payload)
        return message_id

    async def consume_events(
        self,
        stream_name: str,
        group: str,
        consumer: str,
        count: int = 10,
        block: int = 5000,
    ) -> list[tuple[str, dict[str, str]]]:
        """Consume events from a Redis Stream using XREADGROUP."""
        try:
            results = await self.client.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={stream_name: ">"},
                count=count,
                block=block,
            )
            if results:
                # results format: [[stream_name, [(id, data), ...]]]
                return results[0][1]
            return []
        except redis.ResponseError as e:
            if "NOGROUP" in str(e):
                await self.create_consumer_group(stream_name, group)
                return []
            raise

    async def create_consumer_group(
        self, stream_name: str, group: str, start_id: str = "0"
    ) -> None:
        """Create a consumer group for a Redis Stream."""
        try:
            await self.client.xgroup_create(
                name=stream_name, groupname=group, id=start_id, mkstream=True
            )
            logger.info("Created consumer group '%s' for stream '%s'", group, stream_name)
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug("Consumer group '%s' already exists for stream '%s'", group, stream_name)
            else:
                raise


redis_client = RedisClient()
