from __future__ import annotations

import logging

from shapely.geometry import Point, Polygon

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class CrowdDensityPattern(BasePattern):
    """
    Detects when the number of persons in a zone exceeds a threshold.

    Uses temporal threshold: count must exceed max_persons for N consecutive
    frames before triggering.

    This is a scene-level pattern (not per-track), so cooldown uses a
    sentinel key (0) instead of individual track IDs.

    Config:
        zone: list of [x, y] points forming a polygon
        max_persons: maximum allowed persons in zone
        target_classes: list of class names to monitor
        confidence_threshold: minimum detection confidence
        temporal_threshold: consecutive frames before triggering
        severity: event severity level
    """

    COOLDOWN_KEY = 0  # Sentinel for scene-level cooldown

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._consecutive_frames: int = 0

    @property
    def max_persons(self) -> int:
        return self.config.get("max_persons", 10)

    @property
    def target_classes(self) -> list[str]:
        return self.config.get("target_classes", ["person"])

    @property
    def severity(self) -> str:
        return self.config.get("severity", "critical")

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

        # Count persons inside zone
        count = 0
        for track in tracks:
            if track.class_name not in self.target_classes:
                continue
            if track.confidence < self.confidence_threshold:
                continue

            bottom_center = ((track.bbox[0] + track.bbox[2]) / 2, track.bbox[3])
            point = Point(bottom_center[0], bottom_center[1])

            if polygon.contains(point):
                count += 1

        if count > self.max_persons:
            self._consecutive_frames += 1

            if self._consecutive_frames >= self.temporal_threshold and not self.is_in_cooldown(
                self.COOLDOWN_KEY
            ):
                self.mark_triggered(self.COOLDOWN_KEY)
                events.append(
                    PatternEvent(
                        pattern_name=self.name,
                        pattern_type=self.pattern_type,
                        camera_id=self.camera_id,
                        track_id=self.COOLDOWN_KEY,
                        track_internal_id="scene",
                        confidence=1.0,
                        severity=self.severity,
                        metadata={
                            "zone": self.config.get("zone", []),
                            "person_count": count,
                            "max_persons": self.max_persons,
                            "consecutive_frames": self._consecutive_frames,
                        },
                    )
                )
        else:
            self._consecutive_frames = 0

        return events

    def reset(self) -> None:
        super().reset()
        self._consecutive_frames = 0
