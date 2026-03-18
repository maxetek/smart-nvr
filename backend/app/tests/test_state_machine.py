import time

from app.pipeline.models.track import Track, TrackState
from app.pipeline.state_machine import TrackStateMachine


class TestStateMachineTransitions:
    """Tests for TrackStateMachine state transitions."""

    def test_initial_to_tracking_after_confirm_frames(self):
        """Test INITIAL -> TRACKING after enough frames."""
        sm = TrackStateMachine(confirm_frames=3)
        track = Track(track_id=1, state=TrackState.INITIAL, frame_count=3)

        new_state = sm.update(track, is_detected=True)

        assert new_state == TrackState.TRACKING
        assert track.state == TrackState.TRACKING

    def test_initial_stays_initial_before_confirm(self):
        """Test that INITIAL stays INITIAL when frame_count < confirm_frames."""
        sm = TrackStateMachine(confirm_frames=3)
        track = Track(track_id=1, state=TrackState.INITIAL, frame_count=1)

        new_state = sm.update(track, is_detected=True)

        assert new_state is None
        assert track.state == TrackState.INITIAL

    def test_tracking_to_ghost_when_not_detected(self):
        """Test TRACKING -> GHOST when not detected."""
        sm = TrackStateMachine()
        track = Track(track_id=1, state=TrackState.TRACKING)

        new_state = sm.update(track, is_detected=False)

        assert new_state == TrackState.GHOST
        assert track.state == TrackState.GHOST

    def test_initial_to_ghost_when_not_detected(self):
        """Test INITIAL -> GHOST when not detected."""
        sm = TrackStateMachine()
        track = Track(track_id=1, state=TrackState.INITIAL)

        new_state = sm.update(track, is_detected=False)

        assert new_state == TrackState.GHOST
        assert track.state == TrackState.GHOST

    def test_ghost_to_dead_after_timeout(self):
        """Test GHOST -> DEAD after ghost_timeout seconds."""
        sm = TrackStateMachine(ghost_timeout=0.05)
        track = Track(track_id=1, state=TrackState.GHOST)
        # Simulate time passing since last seen
        track.last_seen = time.time() - 0.1

        new_state = sm.update(track, is_detected=False)

        assert new_state == TrackState.DEAD
        assert track.state == TrackState.DEAD

    def test_ghost_stays_ghost_before_timeout(self):
        """Test that GHOST stays GHOST before timeout expires."""
        sm = TrackStateMachine(ghost_timeout=10.0)
        track = Track(track_id=1, state=TrackState.GHOST)

        new_state = sm.update(track, is_detected=False)

        assert new_state is None
        assert track.state == TrackState.GHOST

    def test_ghost_to_tracking_when_redetected(self):
        """Test GHOST -> TRACKING when re-detected."""
        sm = TrackStateMachine()
        track = Track(track_id=1, state=TrackState.GHOST)

        new_state = sm.update(track, is_detected=True)

        assert new_state == TrackState.TRACKING
        assert track.state == TrackState.TRACKING

    def test_dead_stays_dead(self):
        """Test that DEAD tracks never transition."""
        sm = TrackStateMachine()
        track = Track(track_id=1, state=TrackState.DEAD)

        new_state = sm.update(track, is_detected=True)

        assert new_state is None
        assert track.state == TrackState.DEAD

    def test_dead_stays_dead_not_detected(self):
        """Test that DEAD tracks stay dead even when not detected."""
        sm = TrackStateMachine()
        track = Track(track_id=1, state=TrackState.DEAD)

        new_state = sm.update(track, is_detected=False)

        assert new_state is None
        assert track.state == TrackState.DEAD
