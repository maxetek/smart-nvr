import asyncio
import logging
import uuid

from app.database import async_session
from app.models.event import Event
from app.pipeline.event_publisher import STREAM_NAME
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

CONSUMER_GROUP = "event_consumers"
CONSUMER_NAME = "consumer_1"


class EventConsumer:
    """Consumes events from Redis Streams and persists to PostgreSQL."""

    def __init__(
        self,
        stream_name: str = STREAM_NAME,
        group: str = CONSUMER_GROUP,
        consumer: str = CONSUMER_NAME,
        batch_size: int = 50,
        poll_interval: int = 1000,  # ms
    ) -> None:
        self.stream_name = stream_name
        self.group = group
        self.consumer = consumer
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        """Start consuming events."""
        self._running = True

        # Create consumer group if not exists
        await redis_client.create_consumer_group(self.stream_name, self.group)
        logger.info(
            "Event consumer started (group=%s, consumer=%s)", self.group, self.consumer
        )

        while self._running:
            try:
                messages = await redis_client.consume_events(
                    stream_name=self.stream_name,
                    group=self.group,
                    consumer=self.consumer,
                    count=self.batch_size,
                    block=self.poll_interval,
                )

                if messages:
                    await self._process_messages(messages)

            except Exception as e:
                logger.error("Event consumer error: %s", e)
                await asyncio.sleep(1)

    async def _process_messages(self, messages: list) -> None:
        """Process a batch of messages from Redis Stream."""
        events_to_insert: list[Event] = []

        for msg_id, data in messages:
            try:
                event_type = data.get("event_type", "")

                # Only persist confirmed tracks and significant events
                if event_type in ("track_confirmed", "track_lost"):
                    event = self._build_event(data)
                    if event:
                        events_to_insert.append(event)

                # Acknowledge the message
                await redis_client.client.xack(self.stream_name, self.group, msg_id)

            except Exception as e:
                logger.error("Failed to process message %s: %s", msg_id, e)

        # Batch insert events
        if events_to_insert:
            try:
                async with async_session() as session:
                    session.add_all(events_to_insert)
                    await session.commit()
                logger.info("Persisted %d events to database", len(events_to_insert))
            except Exception as e:
                logger.error("Failed to persist events: %s", e)

    def _build_event(self, data: dict[str, str]) -> Event | None:
        """Build an Event model from Redis Stream message data."""
        try:
            camera_id = data.get("camera_id")
            if not camera_id:
                return None

            event_type = data.get("event_type", "detection")
            class_name = data.get("class_name", "unknown")

            # Map to our event types
            if event_type == "track_confirmed":
                mapped_type = f"{class_name}_detected"
            elif event_type == "track_lost":
                mapped_type = f"{class_name}_lost"
            else:
                mapped_type = event_type

            return Event(
                camera_id=uuid.UUID(camera_id),
                event_type=mapped_type,
                severity="info",
                confidence=float(data.get("confidence", 0)),
                metadata_json={
                    "track_id": data.get("track_id"),
                    "internal_id": data.get("internal_id"),
                    "class_id": data.get("class_id"),
                    "class_name": class_name,
                    "state": data.get("state"),
                    "bbox": [
                        float(data.get("bbox_x1", 0)),
                        float(data.get("bbox_y1", 0)),
                        float(data.get("bbox_x2", 0)),
                        float(data.get("bbox_y2", 0)),
                    ],
                },
            )
        except Exception as e:
            logger.error("Failed to build event: %s", e)
            return None

    async def stop(self) -> None:
        """Stop the event consumer."""
        self._running = False
        logger.info("Event consumer stopped")
