from app.pipeline.models.track import Track
from app.pipeline.patterns.ml_based.smoking_pattern import SmokingPattern


def make_track(
    track_id=1,
    bbox=(200, 200, 300, 300),
    class_name="person",
    confidence=0.9,
    smoking_prob=0.0,
):
    t = Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)
    t.attributes["smoking_prob"] = smoking_prob
    return t


def make_pattern(temporal_threshold=3, cooldown=0, zone=None, confidence_threshold=0.5):
    config = {
        "target_classes": ["person"],
        "confidence_threshold": confidence_threshold,
        "temporal_threshold": temporal_threshold,
        "severity": "warning",
    }
    if zone:
        config["zone"] = zone
    return SmokingPattern(
        pattern_id="sp1",
        camera_id="cam1",
        name="Test Smoking",
        pattern_type="smoking",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestSmokingPattern:
    def test_trigger_after_temporal_threshold(self):
        """High smoking_prob for enough frames triggers event."""
        pattern = make_pattern(temporal_threshold=3)
        track = make_track(smoking_prob=0.9)

        # Frames 1-2: no trigger
        for _ in range(2):
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 0

        # Frame 3: trigger
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1
        assert events[0].severity == "warning"
        assert events[0].metadata["smoking_prob"] == 0.9

    def test_no_trigger_low_prob(self):
        """Low smoking_prob does not trigger."""
        pattern = make_pattern(temporal_threshold=1)
        track = make_track(smoking_prob=0.1)

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_counter_resets_on_low_prob(self):
        """Counter resets when prob drops below threshold."""
        pattern = make_pattern(temporal_threshold=3)
        high = make_track(smoking_prob=0.9)
        low = make_track(smoking_prob=0.1)

        # 2 high frames
        pattern.evaluate([high], (480, 640))
        pattern.evaluate([high], (480, 640))
        assert pattern._consecutive_frames.get(1) == 2

        # 1 low frame — resets
        pattern.evaluate([low], (480, 640))
        assert pattern._consecutive_frames.get(1) == 0

    def test_zone_filtering(self):
        """Track outside configured zone is excluded."""
        zone = [[100, 100], [400, 100], [400, 400], [100, 400]]
        pattern = make_pattern(temporal_threshold=1, zone=zone)

        # Center (550, 550) is outside zone
        track = make_track(bbox=(500, 500, 600, 600), smoking_prob=0.9)
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_no_zone_applies_everywhere(self):
        """No zone configured means pattern applies everywhere."""
        pattern = make_pattern(temporal_threshold=1)
        track = make_track(bbox=(500, 500, 600, 600), smoking_prob=0.9)
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

    def test_cooldown(self):
        pattern = make_pattern(temporal_threshold=1, cooldown=300)
        track = make_track(smoking_prob=0.9)

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_cleanup_stale_tracks(self):
        pattern = make_pattern(temporal_threshold=5)
        track = make_track(smoking_prob=0.9)
        pattern.evaluate([track], (480, 640))
        assert 1 in pattern._consecutive_frames

        pattern.evaluate([], (480, 640))
        assert 1 not in pattern._consecutive_frames

    def test_reset(self):
        pattern = make_pattern()
        track = make_track(smoking_prob=0.9)
        pattern.evaluate([track], (480, 640))
        assert len(pattern._consecutive_frames) > 0

        pattern.reset()
        assert len(pattern._consecutive_frames) == 0
