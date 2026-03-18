import time

from app.pipeline.models.track import Track, TrackState


class TestTrackCreation:
    """Tests for Track dataclass creation and defaults."""

    def test_track_creation_with_defaults(self):
        """Test that a Track is created with proper default values."""
        track = Track(track_id=1)
        assert track.track_id == 1
        assert track.class_id == 0
        assert track.class_name == "unknown"
        assert track.state == TrackState.INITIAL
        assert track.bbox == (0.0, 0.0, 0.0, 0.0)
        assert track.confidence == 0.0
        assert track.frame_count == 0
        assert isinstance(track.internal_id, str)
        assert len(track.internal_id) > 0

    def test_track_creation_with_values(self):
        """Test that a Track can be created with explicit values."""
        track = Track(
            track_id=42,
            class_id=0,
            class_name="person",
            state=TrackState.TRACKING,
            bbox=(100.0, 200.0, 300.0, 400.0),
            confidence=0.95,
            frame_count=10,
        )
        assert track.track_id == 42
        assert track.class_name == "person"
        assert track.state == TrackState.TRACKING
        assert track.confidence == 0.95
        assert track.frame_count == 10

    def test_no_shared_mutable_defaults(self):
        """Test that two Track instances do not share the attributes dict."""
        track1 = Track(track_id=1)
        track2 = Track(track_id=2)
        track1.attributes["smoking_prob"] = 0.8
        assert "smoking_prob" not in track2.attributes

    def test_unique_internal_ids(self):
        """Test that each Track gets a unique internal_id."""
        track1 = Track(track_id=1)
        track2 = Track(track_id=2)
        assert track1.internal_id != track2.internal_id


class TestTrackUpdate:
    """Tests for Track.update() method."""

    def test_update_changes_bbox_and_confidence(self):
        """Test that update() modifies bbox, confidence, last_seen, and frame_count."""
        track = Track(track_id=1, bbox=(0.0, 0.0, 10.0, 10.0), confidence=0.5)
        initial_last_seen = track.last_seen
        time.sleep(0.01)

        track.update(bbox=(50.0, 50.0, 150.0, 150.0), confidence=0.9)

        assert track.bbox == (50.0, 50.0, 150.0, 150.0)
        assert track.confidence == 0.9
        assert track.frame_count == 1
        assert track.last_seen > initial_last_seen

    def test_update_increments_frame_count(self):
        """Test that frame_count increments on each update."""
        track = Track(track_id=1)
        assert track.frame_count == 0
        track.update(bbox=(1.0, 1.0, 2.0, 2.0), confidence=0.5)
        assert track.frame_count == 1
        track.update(bbox=(1.0, 1.0, 2.0, 2.0), confidence=0.6)
        assert track.frame_count == 2


class TestTrackProperties:
    """Tests for Track computed properties."""

    def test_age_seconds(self):
        """Test that age_seconds reflects time since creation."""
        track = Track(track_id=1)
        time.sleep(0.05)
        assert track.age_seconds >= 0.04

    def test_time_since_last_seen(self):
        """Test that time_since_last_seen grows after creation."""
        track = Track(track_id=1)
        time.sleep(0.05)
        assert track.time_since_last_seen >= 0.04

    def test_center(self):
        """Test center property calculation."""
        track = Track(track_id=1, bbox=(100.0, 200.0, 300.0, 400.0))
        cx, cy = track.center
        assert cx == 200.0
        assert cy == 300.0
