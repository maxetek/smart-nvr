from app.pipeline.models.track import Track
from app.pipeline.patterns.ml_based.weapon_pattern import WeaponPattern


def make_track(
    track_id=1,
    bbox=(200, 200, 300, 300),
    class_name="person",
    confidence=0.9,
    weapon_prob=0.0,
    weapon_type="none",
):
    t = Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=confidence)
    t.attributes["weapon_prob"] = weapon_prob
    t.attributes["weapon_type"] = weapon_type
    return t


def make_pattern(temporal_threshold=3, cooldown=0, zone=None, confidence_threshold=0.5):
    config = {
        "target_classes": ["person"],
        "confidence_threshold": confidence_threshold,
        "temporal_threshold": temporal_threshold,
        "severity": "critical",
    }
    if zone:
        config["zone"] = zone
    return WeaponPattern(
        pattern_id="wp1",
        camera_id="cam1",
        name="Test Weapon",
        pattern_type="weapon",
        config=config,
        cooldown_seconds=cooldown,
    )


class TestWeaponPattern:
    def test_trigger_with_critical_severity(self):
        """High weapon_prob for enough frames triggers critical event."""
        pattern = make_pattern(temporal_threshold=3)
        track = make_track(weapon_prob=0.95, weapon_type="pistol")

        for _ in range(2):
            events = pattern.evaluate([track], (480, 640))
            assert len(events) == 0

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1
        assert events[0].severity == "critical"
        assert events[0].metadata["weapon_type"] == "pistol"
        assert events[0].metadata["weapon_prob"] == 0.95

    def test_no_trigger_low_prob(self):
        pattern = make_pattern(temporal_threshold=1)
        track = make_track(weapon_prob=0.1)
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_default_temporal_threshold_is_3(self):
        """Weapon pattern defaults to 3 frames for faster response."""
        config = {"target_classes": ["person"], "confidence_threshold": 0.5}
        pattern = WeaponPattern(
            pattern_id="wp2",
            camera_id="cam1",
            name="Default Weapon",
            pattern_type="weapon",
            config=config,
            cooldown_seconds=0,
        )
        assert pattern.temporal_threshold == 3

    def test_zone_filtering(self):
        zone = [[100, 100], [400, 100], [400, 400], [100, 400]]
        pattern = make_pattern(temporal_threshold=1, zone=zone)

        track = make_track(bbox=(500, 500, 600, 600), weapon_prob=0.9)
        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_cooldown(self):
        pattern = make_pattern(temporal_threshold=1, cooldown=300)
        track = make_track(weapon_prob=0.9)

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 1

        events = pattern.evaluate([track], (480, 640))
        assert len(events) == 0

    def test_weapon_type_in_metadata(self):
        pattern = make_pattern(temporal_threshold=1)
        track = make_track(weapon_prob=0.9, weapon_type="rifle")
        events = pattern.evaluate([track], (480, 640))
        assert events[0].metadata["weapon_type"] == "rifle"

    def test_reset(self):
        pattern = make_pattern()
        track = make_track(weapon_prob=0.9)
        pattern.evaluate([track], (480, 640))
        assert len(pattern._consecutive_frames) > 0

        pattern.reset()
        assert len(pattern._consecutive_frames) == 0
