from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrackState(str, Enum):
    """Possible states for a tracked object."""

    INITIAL = "initial"  # Just detected, not yet confirmed
    TRACKING = "tracking"  # Confirmed, actively tracked
    GHOST = "ghost"  # Lost from view, might come back
    DEAD = "dead"  # Gone, will not come back


@dataclass(slots=True)
class Track:
    """Represents a tracked object across frames."""

    track_id: int  # ByteTrack assigned ID
    internal_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Our UUID
    class_id: int = 0
    class_name: str = "unknown"
    state: TrackState = TrackState.INITIAL
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    confidence: float = 0.0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    frame_count: int = 0  # How many frames we've seen this track
    attributes: dict[str, Any] = field(
        default_factory=dict
    )  # For Pattern Engine: smoking_prob, weapon_prob, etc.

    @property
    def age_seconds(self) -> float:
        """Return how long this track has existed."""
        return time.time() - self.first_seen

    @property
    def time_since_last_seen(self) -> float:
        """Return seconds since this track was last detected."""
        return time.time() - self.last_seen

    @property
    def center(self) -> tuple[float, float]:
        """Return the center point of the bounding box."""
        return ((self.bbox[0] + self.bbox[2]) / 2, (self.bbox[1] + self.bbox[3]) / 2)

    def update(self, bbox: tuple[float, float, float, float], confidence: float) -> None:
        """Update track with new detection."""
        self.bbox = bbox
        self.confidence = confidence
        self.last_seen = time.time()
        self.frame_count += 1
