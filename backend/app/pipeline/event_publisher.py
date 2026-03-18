import logging
import time
from typing import Any

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import PatternEvent
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

STREAM_NAME = "smartnvr:events"


class EventPublisher:
    """Publishes pipeline events to Redis Streams."""

    def __init__(self, camera_id: str, stream_name: str = STREAM_NAME) -> None:
        self.camera_id = camera_id
        self.stream_name = stream_name

    async def publish_track_event(
        self, track: Track, event_type: str, extra: dict[str, Any] | None = None
    ) -> str:
        """Publish a track event to Redis Stream."""
        data = {
            "event_type": event_type,
            "camera_id": self.camera_id,
            "track_id": str(track.track_id),
            "internal_id": track.internal_id,
            "class_id": str(track.class_id),
            "class_name": track.class_name,
            "state": track.state.value,
            "bbox_x1": str(track.bbox[0]),
            "bbox_y1": str(track.bbox[1]),
            "bbox_x2": str(track.bbox[2]),
            "bbox_y2": str(track.bbox[3]),
            "confidence": str(track.confidence),
            "timestamp": str(time.time()),
        }
        if extra:
            for k, v in extra.items():
                data[k] = str(v)

        msg_id = await redis_client.publish_event(self.stream_name, data)
        logger.debug(
            "Published %s for track %d on camera %s",
            event_type,
            track.track_id,
            self.camera_id,
        )
        return msg_id

    async def publish_new_track(self, track: Track) -> str:
        """Publish a new_track event."""
        return await self.publish_track_event(track, "new_track")

    async def publish_track_confirmed(self, track: Track) -> str:
        """Publish a track_confirmed event."""
        return await self.publish_track_event(track, "track_confirmed")

    async def publish_track_update(self, track: Track) -> str:
        """Publish a track_update event."""
        return await self.publish_track_event(track, "track_update")

    async def publish_track_lost(self, track: Track) -> str:
        """Publish a track_lost event."""
        return await self.publish_track_event(track, "track_lost")

    async def publish_pattern_event(self, event: PatternEvent) -> str:
        """Publish a pattern event to Redis Stream."""
        data = {
            "event_type": f"pattern_{event.pattern_type}",
            "pattern_name": event.pattern_name,
            "camera_id": event.camera_id,
            "track_id": str(event.track_id),
            "track_internal_id": event.track_internal_id,
            "confidence": str(event.confidence),
            "severity": event.severity,
            "timestamp": str(event.timestamp),
            **{k: str(v) for k, v in event.metadata.items()},
        }
        msg_id = await redis_client.publish_event(self.stream_name, data)
        logger.debug(
            "Published pattern event %s for camera %s",
            event.pattern_type,
            event.camera_id,
        )
        return msg_id
