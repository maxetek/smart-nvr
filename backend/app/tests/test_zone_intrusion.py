from app.pipeline.models.track import Track
from app.pipeline.patterns.rule_based.zone_intrusion import ZoneIntrusionPattern


def make_track(track_id=1, bbox=(200, 200, 300, 300), class_name="person", confidence=0.9):
    return Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)


def make_pattern(zone=None, temporal_threshold=3, cooldown=0, target_classes=None):
    config = {
        "zone": zone or [[100, 100], [400, 100], [400, 400], [100, 400]],
        "target_classes": target_classes or ["person"],
        "confidence_threshold": 0.5,
        "temporal_threshold": temporal_threshold,
        "severity": "warning",
    }
    return ZoneIntrusionPattern(
        pattern_id="zi1",
        camera_id="cam1",
        name="Test Zone",
        pattern_type="zone_intrusion",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestZoneIntrusion:
    def test_trigger_after_temporal_threshold(self):
        """Track inside zone for enough frames triggers event."""
        pattern = make_pattern(temporal_threshold=3)

        # Bottom-center of bbox (200, 200, 300, 300) is (250, 300) — inside zone
        track = make_track(bbox=(200, 200, 300, 300))

        # Frames 1-2: no trigger yet
        for _ in range(2):
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 0

        # Frame 3: trigger
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1
        assert events[0].severity == "warning"
        assert events[0].pattern_type == "zone_intrusion"

    def test_track_outside_no_trigger(self):
        """Track outside zone never triggers."""
        pattern = make_pattern(temporal_threshold=1)

        # Bottom-center of (500, 500, 600, 600) is (550, 600) — outside zone
        track = make_track(bbox=(500, 500, 600, 600))
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_counter_resets_on_leave(self):
        """Counter resets when track leaves zone."""
        pattern = make_pattern(temporal_threshold=3)
        track = make_track(bbox=(200, 200, 300, 300))

        # 2 frames inside
        for _ in range(2):
            pattern.evaluate([track], (480, 640))
        assert pattern._inside_count.get(track.track_id) == 2

        # Track leaves zone
        track_outside = make_track(bbox=(500, 500, 600, 600))
        pattern.evaluate([track_outside], (480, 640))
        assert pattern._inside_count.get(track.track_id) is None

    def test_cooldown(self):
        """Cooldown prevents re-trigger."""
        pattern = make_pattern(temporal_threshold=1, cooldown=300)
        track = make_track(bbox=(200, 200, 300, 300))

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0  # In cooldown

    def test_ignores_non_target_class(self):
        pattern = make_pattern(temporal_threshold=1, target_classes=["person"])
        track = make_track(bbox=(200, 200, 300, 300), class_name="car")
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_no_zone_no_events(self):
        """No zone configured returns empty events."""
        config = {"target_classes": ["person"], "confidence_threshold": 0.5, "temporal_threshold": 1}
        pattern = ZoneIntrusionPattern(
            pattern_id="zi2",
            camera_id="cam1",
            name="No Zone",
            pattern_type="zone_intrusion",
            config=config,
            cooldown_seconds=0,
        )
        track = make_track()
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_cleanup_stale_tracks(self):
        pattern = make_pattern(temporal_threshold=5)
        track = make_track(bbox=(200, 200, 300, 300))
        pattern.evaluate([track], (480, 640))
        assert 1 in pattern._inside_count

        pattern.evaluate([], (480, 640))
        assert 1 not in pattern._inside_count

    def test_reset(self):
        pattern = make_pattern()
        track = make_track(bbox=(200, 200, 300, 300))
        pattern.evaluate([track], (480, 640))
        assert len(pattern._inside_count) > 0

        pattern.reset()
        assert len(pattern._inside_count) == 0
