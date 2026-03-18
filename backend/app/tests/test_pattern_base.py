import time

from app.pipeline.patterns.base import BasePattern, PatternEvent
from app.pipeline.models.track import Track


class DummyPattern(BasePattern):
    """Concrete pattern for testing the base class."""

    def evaluate(self, tracks, frame_shape):
        events = []
        for track in tracks:
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
                        severity="info",
                    )
                )
        return events


def make_track(track_id=1, class_name="person", bbox=(100, 100, 200, 200), confidence=0.9):
    return Track(track_id=track_id, class_name=class_name, bbox=bbox, confidence=confidence)


class TestPatternEvent:
    def test_creation(self):
        event = PatternEvent(
            pattern_name="test",
            pattern_type="test_type",
            camera_id="cam1",
            track_id=1,
            track_internal_id="uid-1",
            confidence=0.95,
            severity="warning",
        )
        assert event.pattern_name == "test"
        assert event.severity == "warning"
        assert event.confidence == 0.95
        assert event.timestamp > 0

    def test_metadata_default(self):
        event = PatternEvent(
            pattern_name="test",
            pattern_type="t",
            camera_id="c",
            track_id=1,
            track_internal_id="u",
            confidence=0.5,
            severity="info",
        )
        assert event.metadata == {}


class TestBasePattern:
    def _make_pattern(self, cooldown=60, config=None):
        return DummyPattern(
            pattern_id="p1",
            camera_id="cam1",
            name="Test Pattern",
            pattern_type="test",
            config=config or {"confidence_threshold": 0.5},
            cooldown_seconds=cooldown,
        )

    def test_properties(self):
        p = self._make_pattern()
        assert p.pattern_id == "p1"
        assert p.camera_id == "cam1"
        assert p.name == "Test Pattern"
        assert p.pattern_type == "test"
        assert p.confidence_threshold == 0.5
        assert p.temporal_threshold == 1  # default
        assert p.enabled is True

    def test_enabled_toggle(self):
        p = self._make_pattern()
        p.enabled = False
        assert p.enabled is False
        p.enabled = True
        assert p.enabled is True

    def test_cooldown(self):
        p = self._make_pattern(cooldown=1)
        track = make_track()
        assert not p.is_in_cooldown(track.track_id)

        p.mark_triggered(track.track_id)
        assert p.is_in_cooldown(track.track_id)

    def test_cooldown_expires(self):
        p = self._make_pattern(cooldown=0)  # 0 second cooldown
        track = make_track()
        p.mark_triggered(track.track_id)
        # With 0 cooldown, it should not be in cooldown (time.time() - last >= 0)
        assert not p.is_in_cooldown(track.track_id)

    def test_evaluate(self):
        p = self._make_pattern(cooldown=0)
        tracks = [make_track(1), make_track(2)]
        events = p.evaluate(tracks, (480, 640))
        assert len(events) == 2
        assert events[0].track_id == 1
        assert events[1].track_id == 2

    def test_evaluate_respects_cooldown(self):
        p = self._make_pattern(cooldown=300)
        tracks = [make_track(1)]
        events = p.evaluate(tracks, (480, 640))
        assert len(events) == 1  # First trigger

        events = p.evaluate(tracks, (480, 640))
        assert len(events) == 0  # In cooldown

    def test_reset(self):
        p = self._make_pattern(cooldown=300)
        track = make_track()
        p.mark_triggered(track.track_id)
        assert p.is_in_cooldown(track.track_id)

        p.reset()
        assert not p.is_in_cooldown(track.track_id)

    def test_update_config(self):
        p = self._make_pattern()
        assert p.confidence_threshold == 0.5
        p.update_config({"confidence_threshold": 0.8})
        assert p.confidence_threshold == 0.8
