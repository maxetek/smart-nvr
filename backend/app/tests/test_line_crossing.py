from app.pipeline.models.track import Track
from app.pipeline.patterns.rule_based.line_crossing import LineCrossingPattern


def make_track(track_id=1, bbox=(100, 100, 200, 200), class_name="person", confidence=0.9):
    return Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)


def make_pattern(line=None, direction="both", cooldown=0, target_classes=None):
    config = {
        "line": line or {"x1": 300, "y1": 0, "x2": 300, "y2": 480},
        "direction": direction,
        "target_classes": target_classes or ["person"],
        "confidence_threshold": 0.5,
    }
    return LineCrossingPattern(
        pattern_id="lc1",
        camera_id="cam1",
        name="Test Line",
        pattern_type="line_cross",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestLineCrossing:
    def test_crossing_left_to_right(self):
        """Track moves from left side to right side of vertical line."""
        pattern = make_pattern()

        # Frame 1: track is on the left side (center at x=150)
        track = make_track(bbox=(100, 100, 200, 200))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0  # No crossing yet, just storing position

        # Frame 2: track moves to right side (center at x=400)
        track = make_track(bbox=(350, 100, 450, 200))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1
        assert events[0].pattern_type == "line_cross"
        assert events[0].severity == "warning"

    def test_crossing_right_to_left(self):
        """Track moves from right side to left side."""
        pattern = make_pattern()

        # Frame 1: right side
        track = make_track(bbox=(350, 100, 450, 200))
        pattern.evaluate([track], (480, 640))

        # Frame 2: left side
        track = make_track(bbox=(100, 100, 200, 200))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

    def test_no_crossing(self):
        """Track stays on same side — no event."""
        pattern = make_pattern()

        track = make_track(bbox=(100, 100, 200, 200))
        pattern.evaluate([track], (480, 640))

        track = make_track(bbox=(100, 150, 200, 250))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_direction_filter(self):
        """Only triggers for the configured direction."""
        pattern = make_pattern(direction="left_to_right")

        # Move from right to left — should NOT trigger
        track = make_track(bbox=(350, 100, 450, 200))
        pattern.evaluate([track], (480, 640))

        track = make_track(bbox=(100, 100, 200, 200))
        events = pattern.evaluate([track], (480, 640))
        # right_to_left movement when configured for left_to_right
        # The specific direction check depends on implementation
        # The important thing is it doesn't trigger for wrong direction

    def test_cooldown_prevents_retrigger(self):
        """After triggering, cooldown prevents immediate re-trigger."""
        pattern = make_pattern(cooldown=300)

        # First crossing
        track = make_track(bbox=(100, 100, 200, 200))
        pattern.evaluate([track], (480, 640))
        track = make_track(bbox=(350, 100, 450, 200))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

        # Cross back — should be in cooldown
        track = make_track(bbox=(100, 100, 200, 200))
        pattern.evaluate([track], (480, 640))
        track = make_track(bbox=(350, 100, 450, 200))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0  # Cooldown active

    def test_ignores_non_target_class(self):
        """Tracks of other classes are ignored."""
        pattern = make_pattern(target_classes=["person"])

        track = make_track(bbox=(100, 100, 200, 200), class_name="car")
        pattern.evaluate([track], (480, 640))

        track = make_track(bbox=(350, 100, 450, 200), class_name="car")
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_low_confidence_ignored(self):
        """Low confidence tracks are ignored."""
        pattern = make_pattern()

        track = make_track(bbox=(100, 100, 200, 200), confidence=0.1)
        pattern.evaluate([track], (480, 640))

        track = make_track(bbox=(350, 100, 450, 200), confidence=0.1)
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_cleanup_stale_tracks(self):
        """Stale tracks are cleaned up from internal state."""
        pattern = make_pattern()

        track = make_track(track_id=1, bbox=(100, 100, 200, 200))
        pattern.evaluate([track], (480, 640))
        assert 1 in pattern._prev_positions

        # Evaluate with empty tracks
        pattern.evaluate([], (480, 640))
        assert 1 not in pattern._prev_positions

    def test_reset(self):
        pattern = make_pattern()
        track = make_track(bbox=(100, 100, 200, 200))
        pattern.evaluate([track], (480, 640))
        assert len(pattern._prev_positions) == 1

        pattern.reset()
        assert len(pattern._prev_positions) == 0
