import time
from unittest.mock import patch

from app.pipeline.models.track import Track
from app.pipeline.patterns.rule_based.loitering import LoiteringPattern


def make_track(track_id=1, bbox=(200, 200, 300, 300), class_name="person", confidence=0.9):
    return Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)


def make_pattern(zone=None, time_threshold=5.0, cooldown=0, target_classes=None):
    config = {
        "zone": zone or [[100, 100], [400, 100], [400, 400], [100, 400]],
        "time_threshold_seconds": time_threshold,
        "target_classes": target_classes or ["person"],
        "confidence_threshold": 0.5,
        "severity": "warning",
    }
    return LoiteringPattern(
        pattern_id="lo1",
        camera_id="cam1",
        name="Test Loiter",
        pattern_type="loitering",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestLoitering:
    def test_trigger_after_time_threshold(self):
        """Track in zone longer than threshold triggers event."""
        pattern = make_pattern(time_threshold=2.0)
        track = make_track(bbox=(200, 200, 300, 300))

        # First frame — starts timer
        base_time = time.time()
        with patch("app.pipeline.patterns.rule_based.loitering.time") as mock_time:
            mock_time.time.return_value = base_time
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 0

            # 1 second later — not enough
            mock_time.time.return_value = base_time + 1.0
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 0

            # 2.5 seconds later — should trigger
            mock_time.time.return_value = base_time + 2.5
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 1
            assert events[0].severity == "warning"
            assert events[0].metadata["loiter_seconds"] >= 2.0

    def test_no_trigger_before_threshold(self):
        """Track in zone for less than threshold does not trigger."""
        pattern = make_pattern(time_threshold=30.0)
        track = make_track(bbox=(200, 200, 300, 300))

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_timer_resets_on_leave(self):
        """Timer resets when track leaves zone."""
        pattern = make_pattern(time_threshold=2.0)
        track_inside = make_track(bbox=(200, 200, 300, 300))
        track_outside = make_track(bbox=(500, 500, 600, 600))

        base_time = time.time()
        with patch("app.pipeline.patterns.rule_based.loitering.time") as mock_time:
            # Enter zone
            mock_time.time.return_value = base_time
            pattern.evaluate([track_inside], (480, 640))
            assert 1 in pattern._entry_times

            # Leave zone
            mock_time.time.return_value = base_time + 1.0
            pattern.evaluate([track_outside], (480, 640))
            assert 1 not in pattern._entry_times

    def test_track_outside_zone(self):
        """Track completely outside zone does nothing."""
        pattern = make_pattern()
        track = make_track(bbox=(500, 500, 600, 600))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_cooldown(self):
        """Cooldown prevents re-trigger."""
        pattern = make_pattern(time_threshold=0, cooldown=300)
        track = make_track(bbox=(200, 200, 300, 300))

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_reset(self):
        pattern = make_pattern()
        track = make_track(bbox=(200, 200, 300, 300))
        pattern.evaluate([track], (480, 640))
        assert len(pattern._entry_times) > 0

        pattern.reset()
        assert len(pattern._entry_times) == 0
