import logging
from typing import Any

from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent

logger = logging.getLogger(__name__)


class PatternEngine:
    """
    Orchestrates all registered patterns for a camera.
    Runs each enabled pattern against current tracks and collects events.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, BasePattern] = {}  # pattern_id -> pattern

    def add_pattern(self, pattern: BasePattern) -> None:
        self._patterns[pattern.pattern_id] = pattern
        logger.info("Pattern added: %s (%s)", pattern.name, pattern.pattern_type)

    def remove_pattern(self, pattern_id: str) -> None:
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            logger.info("Pattern removed: %s", pattern_id)

    def update_pattern_config(self, pattern_id: str, config: dict[str, Any]) -> None:
        if pattern_id in self._patterns:
            self._patterns[pattern_id].update_config(config)

    def enable_pattern(self, pattern_id: str) -> None:
        if pattern_id in self._patterns:
            self._patterns[pattern_id].enabled = True

    def disable_pattern(self, pattern_id: str) -> None:
        if pattern_id in self._patterns:
            self._patterns[pattern_id].enabled = False

    def evaluate(
        self, tracks: list[Track], frame_shape: tuple[int, int]
    ) -> list[PatternEvent]:
        """Run all enabled patterns and return collected events."""
        all_events: list[PatternEvent] = []

        for pattern in self._patterns.values():
            if not pattern.enabled:
                continue
            try:
                events = pattern.evaluate(tracks, frame_shape)
                all_events.extend(events)
            except Exception as e:
                logger.error("Pattern '%s' evaluation failed: %s", pattern.name, e)

        return all_events

    @property
    def patterns(self) -> dict[str, BasePattern]:
        return self._patterns.copy()

    def reset_all(self) -> None:
        for pattern in self._patterns.values():
            pattern.reset()
