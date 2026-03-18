from app.pipeline.models.track import Track
from app.pipeline.patterns.rule_based.crowd_density import CrowdDensityPattern


def make_track(track_id=1, bbox=(200, 200, 300, 300), class_name="person", confidence=0.9):
    return Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)


def make_tracks_in_zone(n, base_x=150, spacing=30):
    """Create n person tracks all inside the zone."""
    tracks = []
    for i in range(n):
        x = base_x + i * spacing
        tracks.append(make_track(track_id=i + 1, bbox=(x, 200, x + 50, 300)))
    return tracks


def make_pattern(zone=None, max_persons=3, temporal_threshold=2, cooldown=0):
    config = {
        "zone": zone or [[100, 100], [500, 100], [500, 400], [100, 400]],
        "max_persons": max_persons,
        "target_classes": ["person"],
        "confidence_threshold": 0.5,
        "temporal_threshold": temporal_threshold,
        "severity": "critical",
    }
    return CrowdDensityPattern(
        pattern_id="cd1",
        camera_id="cam1",
        name="Test Crowd",
        pattern_type="crowd",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestCrowdDensity:
    def test_trigger_after_temporal_threshold(self):
        """Count exceeds max_persons for enough frames triggers event."""
        pattern = make_pattern(max_persons=3, temporal_threshold=2)
        tracks = make_tracks_in_zone(5)  # 5 > 3

        # Frame 1: consecutive = 1, no trigger
        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 0

        # Frame 2: consecutive = 2, trigger
        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 1
        assert events[0].severity == "critical"
        assert events[0].metadata["person_count"] == 5
        assert events[0].metadata["max_persons"] == 3

    def test_no_trigger_below_threshold(self):
        """Count below max_persons does not trigger."""
        pattern = make_pattern(max_persons=10, temporal_threshold=1)
        tracks = make_tracks_in_zone(3)  # 3 <= 10

        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 0

    def test_counter_resets_when_count_drops(self):
        """Consecutive counter resets when count drops below max."""
        pattern = make_pattern(max_persons=3, temporal_threshold=3)
        many_tracks = make_tracks_in_zone(5)
        few_tracks = make_tracks_in_zone(2)

        # 2 frames above threshold
        pattern.evaluate(many_tracks, (480, 640))
        pattern.evaluate(many_tracks, (480, 640))
        assert pattern._consecutive_frames == 2

        # 1 frame below threshold — resets
        pattern.evaluate(few_tracks, (480, 640))
        assert pattern._consecutive_frames == 0

    def test_cooldown(self):
        """Cooldown prevents re-trigger."""
        pattern = make_pattern(max_persons=3, temporal_threshold=1, cooldown=300)
        tracks = make_tracks_in_zone(5)

        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 1

        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 0  # In cooldown

    def test_scene_level_event(self):
        """Crowd density events use sentinel track_id."""
        pattern = make_pattern(max_persons=1, temporal_threshold=1)
        tracks = make_tracks_in_zone(3)

        events = pattern.evaluate(tracks, (480, 640))
        assert len(events) == 1
        assert events[0].track_id == CrowdDensityPattern.COOLDOWN_KEY
        assert events[0].track_internal_id == "scene"

    def test_reset(self):
        pattern = make_pattern(max_persons=1, temporal_threshold=5)
        tracks = make_tracks_in_zone(3)
        pattern.evaluate(tracks, (480, 640))
        assert pattern._consecutive_frames > 0

        pattern.reset()
        assert pattern._consecutive_frames == 0
