from __future__ import annotations

import logging
import time

from shapely.geometry import Point, Polygon

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class LoiteringPattern(BasePattern):
    """
    Detects when a tracked object remains in a zone longer than a time threshold.

    Tracks entry time for each object. If the object stays in the zone
    longer than time_threshold_seconds, an event is triggered.

    Config:
        zone: list of [x, y] points forming a polygon
        time_threshold_seconds: seconds before triggering (default: 30)
        target_classes: list of class names to monitor
        confidence_threshold: minimum detection confidence
        severity: event severity level
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._entry_times: dict[int, float] = {}  # track_id -> entry timestamp

    @property
    def time_threshold_seconds(self) -> float:
        return self.config.get("time_threshold_seconds", 30)

    @property
    def target_classes(self) -> list[str]:
        return self.config.get("target_classes", ["person"])

    @property
    def severity(self) -> str:
        return self.config.get("severity", "warning")

    def _get_polygon(self) -> Polygon | None:
        zone = self.config.get("zone")
        if not zone or len(zone) < 3:
            return None
        return Polygon(zone)

    def evaluate(
        self, tracks: list[Track], frame_shape: tuple[int, int]
    ) -> list[PatternEvent]:
        events: list[PatternEvent] = []
        polygon = self._get_polygon()
        if polygon is None:
            return events

        now = time.time()
        active_ids: set[int] = set()

        for track in tracks:
            if track.class_name not in self.target_classes:
                continue
            if track.confidence < self.confidence_threshold:
                continue

            active_ids.add(track.track_id)

            bottom_center = ((track.bbox[0] + track.bbox[2]) / 2, track.bbox[3])
            point = Point(bottom_center[0], bottom_center[1])

            if polygon.contains(point):
                if track.track_id not in self._entry_times:
                    self._entry_times[track.track_id] = now

                elapsed = now - self._entry_times[track.track_id]

                if elapsed >= self.time_threshold_seconds and not self.is_in_cooldown(
                    track.track_id
                ):
                    self.mark_triggered(track.track_id)
                    events.append(
                        PatternEvent(
                            pattern_name=self.name,
                            pattern_type=self.pattern_type,
                            camera_id=self.camera_id,
                            track_id=track.track_id,
                            track_internal_id=track.internal_id,
                            confidence=track.confidence,
                            severity=self.severity,
                            metadata={
                                "zone": self.config.get("zone", []),
                                "bbox": list(track.bbox),
                                "loiter_seconds": round(elapsed, 1),
                            },
                        )
                    )
            else:
                # Reset timer when person leaves zone
                self._entry_times.pop(track.track_id, None)

        # Cleanup stale tracks
        for tid in list(self._entry_times):
            if tid not in active_ids:
                del self._entry_times[tid]

        return events

    def reset(self) -> None:
        super().reset()
        self._entry_times.clear()
