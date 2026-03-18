from app.pipeline.models.track import Track
from app.pipeline.patterns.base import BasePattern, PatternEvent
from app.pipeline.patterns.pattern_engine import PatternEngine
from app.pipeline.patterns.pattern_registry import PATTERN_TYPES, create_pattern


class AlwaysTriggerPattern(BasePattern):
    """A pattern that always triggers for testing."""

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
                        confidence=1.0,
                        severity="info",
                    )
                )
        return events


class NeverTriggerPattern(BasePattern):
    """A pattern that never triggers."""

    def evaluate(self, tracks, frame_shape):
        return []


class ErrorPattern(BasePattern):
    """A pattern that raises an error."""

    def evaluate(self, tracks, frame_shape):
        raise RuntimeError("Pattern failed!")


def make_track(track_id=1):
    return Track(track_id=track_id, class_name="person", confidence=0.9)


def make_always_pattern(pattern_id="p1"):
    return AlwaysTriggerPattern(
        pattern_id=pattern_id,
        camera_id="cam1",
        name="Always",
        pattern_type="test",
        config={},
        cooldown_seconds=0,
    )


def make_never_pattern(pattern_id="p2"):
    return NeverTriggerPattern(
        pattern_id=pattern_id,
        camera_id="cam1",
        name="Never",
        pattern_type="test",
        config={},
        cooldown_seconds=0,
    )


class TestPatternEngine:
    def test_add_and_run(self):
        engine = PatternEngine()
        engine.add_pattern(make_always_pattern())

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 1

    def test_multiple_patterns(self):
        engine = PatternEngine()
        engine.add_pattern(make_always_pattern("p1"))
        engine.add_pattern(make_always_pattern("p2"))

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 2

    def test_disabled_pattern_not_run(self):
        engine = PatternEngine()
        p = make_always_pattern()
        engine.add_pattern(p)
        engine.disable_pattern(p.pattern_id)

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 0

    def test_enable_pattern(self):
        engine = PatternEngine()
        p = make_always_pattern()
        engine.add_pattern(p)
        engine.disable_pattern(p.pattern_id)
        engine.enable_pattern(p.pattern_id)

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 1

    def test_remove_pattern(self):
        engine = PatternEngine()
        p = make_always_pattern()
        engine.add_pattern(p)
        engine.remove_pattern(p.pattern_id)

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 0

    def test_error_in_pattern_does_not_crash(self):
        engine = PatternEngine()
        error_pattern = ErrorPattern(
            pattern_id="err",
            camera_id="cam1",
            name="Error",
            pattern_type="test",
            config={},
        )
        good_pattern = make_always_pattern("good")
        engine.add_pattern(error_pattern)
        engine.add_pattern(good_pattern)

        # Should not raise; error pattern is caught, good pattern still runs
        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 1

    def test_patterns_property(self):
        engine = PatternEngine()
        p = make_always_pattern()
        engine.add_pattern(p)
        assert p.pattern_id in engine.patterns

    def test_reset_all(self):
        engine = PatternEngine()
        p = make_always_pattern()
        p.cooldown_seconds = 300
        engine.add_pattern(p)

        engine.evaluate([make_track()], (480, 640))
        assert len(p._last_triggered) > 0

        engine.reset_all()
        assert len(p._last_triggered) == 0

    def test_update_config(self):
        engine = PatternEngine()
        p = make_always_pattern()
        engine.add_pattern(p)
        engine.update_pattern_config(p.pattern_id, {"new_key": "value"})
        assert p.config.get("new_key") == "value"

    def test_events_collected_from_mixed_patterns(self):
        engine = PatternEngine()
        engine.add_pattern(make_always_pattern("p1"))
        engine.add_pattern(make_never_pattern("p2"))
        engine.add_pattern(make_always_pattern("p3"))

        events = engine.evaluate([make_track()], (480, 640))
        assert len(events) == 2  # p1 and p3


class TestPatternRegistry:
    def test_all_types_registered(self):
        expected = {"line_cross", "zone_intrusion", "loitering", "crowd", "smoking", "weapon"}
        assert set(PATTERN_TYPES.keys()) == expected

    def test_create_pattern(self):
        p = create_pattern(
            pattern_id="test1",
            camera_id="cam1",
            name="Test",
            pattern_type="line_cross",
            config={"line": {"x1": 0, "y1": 0, "x2": 100, "y2": 100}},
        )
        assert p.pattern_type == "line_cross"
        assert p.name == "Test"

    def test_create_all_types(self):
        for ptype in PATTERN_TYPES:
            p = create_pattern(
                pattern_id=f"test-{ptype}",
                camera_id="cam1",
                name=f"Test {ptype}",
                pattern_type=ptype,
                config={},
            )
            assert isinstance(p, BasePattern)

    def test_unknown_type_raises(self):
        import pytest

        with pytest.raises(ValueError, match="Unknown pattern type"):
            create_pattern(
                pattern_id="x",
                camera_id="c",
                name="n",
                pattern_type="nonexistent",
                config={},
            )
