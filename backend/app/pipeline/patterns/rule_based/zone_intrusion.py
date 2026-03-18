from __future__ import annotations

import logging

from shapely.geometry import Point, Polygon

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class ZoneIntrusionPattern(BasePattern):
    """
    Detects when a tracked object enters a defined polygon zone.

    Uses temporal threshold: track must be inside for N consecutive frames
    before triggering to prevent false positives from brief overlaps.

    Config:
        zone: list of [x, y] points forming a polygon
        target_classes: list of class names to monitor
        confidence_threshold: minimum detection confidence
        temporal_threshold: consecutive frames inside zone before triggering
        severity: event severity level
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._inside_count: dict[int, int] = {}  # track_id -> consecutive frames inside

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

        active_ids: set[int] = set()

        for track in tracks:
            if track.class_name not in self.target_classes:
                continue
            if track.confidence < self.confidence_threshold:
                continue

            active_ids.add(track.track_id)

            # Use bottom-center of bbox for ground position
            bottom_center = ((track.bbox[0] + track.bbox[2]) / 2, track.bbox[3])
            point = Point(bottom_center[0], bottom_center[1])

            if polygon.contains(point):
                count = self._inside_count.get(track.track_id, 0) + 1
                self._inside_count[track.track_id] = count

                if count >= self.temporal_threshold and not self.is_in_cooldown(
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
                                "consecutive_frames": count,
                            },
                        )
                    )
            else:
                # Reset counter when track leaves zone
                self._inside_count.pop(track.track_id, None)

        # Cleanup stale tracks
        for tid in list(self._inside_count):
            if tid not in active_ids:
                del self._inside_count[tid]

        return events

    def reset(self) -> None:
        super().reset()
        self._inside_count.clear()
