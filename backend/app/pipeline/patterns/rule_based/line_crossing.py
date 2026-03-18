from __future__ import annotations

import logging

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class LineCrossingPattern(BasePattern):
    """
    Detects when a tracked object crosses a defined line.

    Uses cross-product to determine which side of the line the object center is on,
    and triggers when it moves from one side to the other.

    Config:
        line: {x1, y1, x2, y2} — line endpoints in pixel coordinates
        direction: "both" | "left_to_right" | "right_to_left" |
                   "top_to_bottom" | "bottom_to_top"
        target_classes: list of class names to monitor
        confidence_threshold: minimum detection confidence
        temporal_threshold: consecutive frames (unused for line crossing, crossing is instant)
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._prev_positions: dict[int, tuple[float, float]] = {}

    @property
    def direction(self) -> str:
        return self.config.get("direction", "both")

    @property
    def target_classes(self) -> list[str]:
        return self.config.get("target_classes", ["person"])

    def _get_line(self) -> tuple[tuple[float, float], tuple[float, float]]:
        line = self.config.get("line", {})
        start = (float(line.get("x1", 0)), float(line.get("y1", 0)))
        end = (float(line.get("x2", 0)), float(line.get("y2", 0)))
        return start, end

    @staticmethod
    def _side_of_line(
        point: tuple[float, float],
        line_start: tuple[float, float],
        line_end: tuple[float, float],
    ) -> float:
        """Returns positive if point is on left side, negative if right, 0 if on line."""
        return (line_end[0] - line_start[0]) * (point[1] - line_start[1]) - (
            line_end[1] - line_start[1]
        ) * (point[0] - line_start[0])

    def _check_direction(
        self, prev_side: float, curr_side: float, line_start: tuple[float, float],
        line_end: tuple[float, float],
    ) -> bool:
        """Check if the crossing direction matches the configured direction."""
        direction = self.direction
        if direction == "both":
            return True

        # Determine crossing direction based on line orientation
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]

        # For a primarily horizontal line (|dx| > |dy|):
        #   left_to_right means going from negative y to positive y side
        #   top_to_bottom means going from negative side to positive side
        # For a primarily vertical line:
        #   similar logic applies

        crossed_positive = prev_side < 0 and curr_side > 0
        crossed_negative = prev_side > 0 and curr_side < 0

        if direction == "left_to_right":
            return crossed_positive if abs(dy) > abs(dx) else crossed_positive
        elif direction == "right_to_left":
            return crossed_negative if abs(dy) > abs(dx) else crossed_negative
        elif direction == "top_to_bottom":
            return crossed_positive if abs(dx) > abs(dy) else crossed_positive
        elif direction == "bottom_to_top":
            return crossed_negative if abs(dx) > abs(dy) else crossed_negative

        return True

    def evaluate(
        self, tracks: list[Track], frame_shape: tuple[int, int]
    ) -> list[PatternEvent]:
        events: list[PatternEvent] = []
        line_start, line_end = self._get_line()
        active_ids: set[int] = set()

        for track in tracks:
            if track.class_name not in self.target_classes:
                continue
            if track.confidence < self.confidence_threshold:
                continue

            active_ids.add(track.track_id)
            center = track.center
            curr_side = self._side_of_line(center, line_start, line_end)
            prev_pos = self._prev_positions.get(track.track_id)

            if prev_pos is not None:
                prev_side = self._side_of_line(prev_pos, line_start, line_end)

                # Check if crossed (sides changed and neither is zero)
                if prev_side != 0 and curr_side != 0 and (
                    (prev_side > 0 and curr_side < 0) or (prev_side < 0 and curr_side > 0)
                ):
                    if self._check_direction(prev_side, curr_side, line_start, line_end):
                        if not self.is_in_cooldown(track.track_id):
                            self.mark_triggered(track.track_id)
                            events.append(
                                PatternEvent(
                                    pattern_name=self.name,
                                    pattern_type=self.pattern_type,
                                    camera_id=self.camera_id,
                                    track_id=track.track_id,
                                    track_internal_id=track.internal_id,
                                    confidence=track.confidence,
                                    severity="warning",
                                    metadata={
                                        "direction": self.direction,
                                        "line": self.config.get("line", {}),
                                        "bbox": list(track.bbox),
                                        "crossing_point": list(center),
                                    },
                                )
                            )

            self._prev_positions[track.track_id] = center

        # Cleanup stale tracks
        for tid in list(self._prev_positions):
            if tid not in active_ids:
                del self._prev_positions[tid]

        return events

    def reset(self) -> None:
        super().reset()
        self._prev_positions.clear()
