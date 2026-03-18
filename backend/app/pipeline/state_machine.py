import logging

from app.pipeline.models.track import Track, TrackState

logger = logging.getLogger(__name__)


class TrackStateMachine:
    """Manages track state transitions and emits events on transitions."""

    def __init__(
        self,
        confirm_frames: int = 3,  # Frames to move INITIAL -> TRACKING
        ghost_timeout: float = 2.0,  # Seconds before GHOST -> DEAD
    ):
        self.confirm_frames = confirm_frames
        self.ghost_timeout = ghost_timeout

    def update(self, track: Track, is_detected: bool) -> TrackState | None:
        """
        Update a track's state based on whether it was detected this frame.

        Returns the NEW state if a transition occurred, None otherwise.
        """
        old_state = track.state

        if track.state == TrackState.DEAD:
            return None  # Dead tracks don't transition

        if is_detected:
            if track.state == TrackState.INITIAL:
                if track.frame_count >= self.confirm_frames:
                    track.state = TrackState.TRACKING
            elif track.state == TrackState.GHOST:
                track.state = TrackState.TRACKING  # Recovered
        else:
            if track.state in (TrackState.INITIAL, TrackState.TRACKING):
                track.state = TrackState.GHOST
            elif track.state == TrackState.GHOST:
                if track.time_since_last_seen > self.ghost_timeout:
                    track.state = TrackState.DEAD

        if track.state != old_state:
            logger.debug(
                "Track %d: %s -> %s",
                track.track_id,
                old_state.value,
                track.state.value,
            )
            return track.state
        return None
