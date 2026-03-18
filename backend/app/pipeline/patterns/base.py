from __future__ import annotations

import abc
import time
import logging
from dataclasses import dataclass, field
from typing import Any

from app.pipeline.models.track import Track

logger = logging.getLogger(__name__)


@dataclass
class PatternEvent:
    """Event emitted when a pattern is triggered."""

    pattern_name: str
    pattern_type: str
    camera_id: str
    track_id: int
    track_internal_id: str
    confidence: float
    severity: str  # info, warning, critical
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class BasePattern(abc.ABC):
    """
    Abstract base class for all detection patterns.

    Every pattern has 3 configurable controls:
    1. confidence_threshold — minimum ML confidence to consider
    2. temporal_threshold — how many consecutive frames/seconds before triggering
    3. spatial_rule — where the pattern applies (zone polygon, line coordinates)

    Plus a cooldown to prevent repeated triggers.
    """

    def __init__(
        self,
        pattern_id: str,
        camera_id: str,
        name: str,
        pattern_type: str,
        config: dict[str, Any],
        cooldown_seconds: int = 60,
    ) -> None:
        self.pattern_id = pattern_id
        self.camera_id = camera_id
        self.name = name
        self.pattern_type = pattern_type
        self.config = config
        self.cooldown_seconds = cooldown_seconds
        self._last_triggered: dict[int, float] = {}  # track_id -> last trigger time
        self._enabled = True

    @property
    def confidence_threshold(self) -> float:
        return self.config.get("confidence_threshold", 0.5)

    @property
    def temporal_threshold(self) -> int:
        """Number of consecutive frames required before triggering."""
        return self.config.get("temporal_threshold", 1)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def is_in_cooldown(self, track_id: int) -> bool:
        last = self._last_triggered.get(track_id, 0)
        return (time.time() - last) < self.cooldown_seconds

    def mark_triggered(self, track_id: int) -> None:
        self._last_triggered[track_id] = time.time()

    @abc.abstractmethod
    def evaluate(
        self, tracks: list[Track], frame_shape: tuple[int, int]
    ) -> list[PatternEvent]:
        """
        Evaluate pattern against current tracks.

        Args:
            tracks: List of currently active tracks
            frame_shape: (height, width) of the current frame

        Returns:
            List of PatternEvent for each triggered detection
        """
        ...

    def update_config(self, config: dict[str, Any]) -> None:
        """Update pattern configuration dynamically."""
        self.config = config

    def reset(self) -> None:
        """Reset internal state."""
        self._last_triggered.clear()
