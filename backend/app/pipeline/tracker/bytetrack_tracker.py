import logging
import time

import numpy as np
import supervision as sv

from app.pipeline.models.detection import Detection
from app.pipeline.models.track import Track, TrackState

logger = logging.getLogger(__name__)


class ByteTrackConfig:
    """Configuration for the ByteTrack tracker."""

    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,  # frames before GHOST -> DEAD
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 15,
        minimum_consecutive_frames: int = 3,  # frames before INITIAL -> TRACKING
    ):
        self.track_activation_threshold = track_activation_threshold
        self.lost_track_buffer = lost_track_buffer
        self.minimum_matching_threshold = minimum_matching_threshold
        self.frame_rate = frame_rate
        self.minimum_consecutive_frames = minimum_consecutive_frames


class ByteTrackTracker:
    """Wrapper around supervision.ByteTrack for consistent tracking."""

    def __init__(self, config: ByteTrackConfig | None = None) -> None:
        self.config = config or ByteTrackConfig()
        self._tracker = sv.ByteTrack(
            track_activation_threshold=self.config.track_activation_threshold,
            lost_track_buffer=self.config.lost_track_buffer,
            minimum_matching_threshold=self.config.minimum_matching_threshold,
            frame_rate=self.config.frame_rate,
            minimum_consecutive_frames=self.config.minimum_consecutive_frames,
        )
        self._tracks: dict[int, Track] = {}  # tracker_id -> Track

    def update(self, detections: list[Detection]) -> list[Track]:
        """Update tracker with new detections. Returns active tracks."""
        if not detections:
            # Still need to update tracker with empty detections for timeout logic
            sv_detections = sv.Detections.empty()
        else:
            bboxes = np.array([d.bbox for d in detections], dtype=np.float32)
            confs = np.array([d.confidence for d in detections], dtype=np.float32)
            class_ids = np.array([d.class_id for d in detections], dtype=int)
            sv_detections = sv.Detections(
                xyxy=bboxes,
                confidence=confs,
                class_id=class_ids,
            )

        # Run ByteTrack
        tracked = self._tracker.update_with_detections(sv_detections)

        # Map tracker IDs back to Track objects
        active_tracker_ids: set[int] = set()
        active_tracks: list[Track] = []

        if tracked.tracker_id is not None:
            for i, tracker_id in enumerate(tracked.tracker_id):
                tid = int(tracker_id)
                active_tracker_ids.add(tid)
                bbox = tuple(float(x) for x in tracked.xyxy[i])
                conf = (
                    float(tracked.confidence[i]) if tracked.confidence is not None else 0.0
                )
                cls_id = int(tracked.class_id[i]) if tracked.class_id is not None else 0

                if tid in self._tracks:
                    # Existing track — update
                    track = self._tracks[tid]
                    track.update(bbox=bbox, confidence=conf)
                    if track.state == TrackState.GHOST:
                        track.state = TrackState.TRACKING  # Re-appeared
                    elif (
                        track.state == TrackState.INITIAL
                        and track.frame_count >= self.config.minimum_consecutive_frames
                    ):
                        track.state = TrackState.TRACKING
                else:
                    # New track
                    cls_name = self._find_class_name(bbox, detections, cls_id)
                    track = Track(
                        track_id=tid,
                        class_id=cls_id,
                        class_name=cls_name,
                        bbox=bbox,
                        confidence=conf,
                        state=TrackState.INITIAL,
                        frame_count=1,
                    )
                    self._tracks[tid] = track

                active_tracks.append(track)

        # Mark lost tracks as GHOST or DEAD
        for tid, track in list(self._tracks.items()):
            if tid not in active_tracker_ids and track.state not in (TrackState.DEAD,):
                if track.state == TrackState.GHOST:
                    # Already ghost — check if it should die
                    if track.time_since_last_seen > (
                        self.config.lost_track_buffer / max(self.config.frame_rate, 1)
                    ):
                        track.state = TrackState.DEAD
                else:
                    track.state = TrackState.GHOST

        # Clean up dead tracks periodically (keep last 60s for reference)
        self._cleanup_dead_tracks()

        return active_tracks

    def _find_class_name(
        self, bbox: tuple, detections: list[Detection], cls_id: int
    ) -> str:
        """Find class name from original detections matching this bbox."""
        for det in detections:
            if det.class_id == cls_id:
                return det.class_name
        return f"class_{cls_id}"

    def _cleanup_dead_tracks(self, max_age: float = 60.0) -> None:
        """Remove dead tracks older than max_age seconds."""
        now = time.time()
        dead_ids = [
            tid
            for tid, track in self._tracks.items()
            if track.state == TrackState.DEAD and (now - track.last_seen) > max_age
        ]
        for tid in dead_ids:
            del self._tracks[tid]

    def get_track(self, track_id: int) -> Track | None:
        """Get a track by its tracker ID."""
        return self._tracks.get(track_id)

    def get_all_tracks(self) -> dict[int, Track]:
        """Return a copy of all known tracks."""
        return self._tracks.copy()

    def reset(self) -> None:
        """Reset the tracker and clear all tracks."""
        self._tracker.reset()
        self._tracks.clear()
