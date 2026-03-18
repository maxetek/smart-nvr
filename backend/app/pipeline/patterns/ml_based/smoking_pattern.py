from __future__ import annotations

import logging

from shapely.geometry import Point, Polygon

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class SmokingPattern(BasePattern):
    """
    ML-based smoking detection pattern.

    Uses temporal smoothing: smoking_prob must exceed threshold
    for N consecutive frames before triggering.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._consecutive_frames: dict[int, int] = {}  # track_id -> consecutive high frames

    @property
    def severity(self) -> str:
        return self.config.get("severity", "warning")

    @property
    def target_classes(self) -> list[str]:
        return self.config.get("target_classes", ["person"])

    def evaluate(
        self, tracks: list[Track], frame_shape: tuple[int, int]
    ) -> list[PatternEvent]:
        events: list[PatternEvent] = []
        active_ids: set[int] = set()

        for track in tracks:
            if track.class_name not in self.target_classes:
                continue

            active_ids.add(track.track_id)
            smoking_prob = track.attributes.get("smoking_prob", 0.0)

            # Check spatial rule (zone) if configured
            if not self._is_in_zone(track, frame_shape):
                self._consecutive_frames.pop(track.track_id, None)
                continue

            if smoking_prob >= self.confidence_threshold:
                count = self._consecutive_frames.get(track.track_id, 0) + 1
                self._consecutive_frames[track.track_id] = count

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
                            confidence=smoking_prob,
                            severity=self.severity,
                            metadata={
                                "smoking_prob": smoking_prob,
                                "consecutive_frames": count,
                                "bbox": list(track.bbox),
                            },
                        )
                    )
            else:
                self._consecutive_frames[track.track_id] = 0

        # Cleanup tracks no longer active
        for tid in list(self._consecutive_frames):
            if tid not in active_ids:
                del self._consecutive_frames[tid]

        return events

    def _is_in_zone(self, track: Track, frame_shape: tuple[int, int]) -> bool:
        """Check if track is in the configured zone. If no zone, return True."""
        zone = self.config.get("zone")
        if not zone:
            return True
        poly = Polygon(zone)
        center = track.center
        return poly.contains(Point(center[0], center[1]))

    def reset(self) -> None:
        super().reset()
        self._consecutive_frames.clear()
