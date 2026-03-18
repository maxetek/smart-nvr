import numpy as np

from app.pipeline.attributes.base import AttributeModel
from app.pipeline.attributes.cascade_pipeline import CascadeAttributePipeline
from app.pipeline.attributes.registry import AttributeModelRegistry
from app.pipeline.models.track import Track


class MockModel(AttributeModel):
    """Mock attribute model for testing."""

    def __init__(self, name_val="mock", classes=None, result=None):
        self._name = name_val
        self._classes = classes or ["person"]
        self._result = result or {"mock_attr": 0.75}
        self._infer_count = 0

    @property
    def name(self):
        return self._name

    @property
    def target_classes(self):
        return self._classes

    def load(self):
        pass

    def infer(self, crop):
        self._infer_count += 1
        return self._result.copy()

    def unload(self):
        pass


def make_track(track_id=1, bbox=(100, 100, 200, 200), class_name="person"):
    return Track(track_id=track_id, bbox=bbox, class_name=class_name, confidence=0.9)


def make_frame(h=480, w=640):
    return np.zeros((h, w, 3), dtype=np.uint8)


class TestCascadeAttributePipeline:
    def test_updates_track_attributes(self):
        registry = AttributeModelRegistry()
        model = MockModel(result={"smoking_prob": 0.85})
        registry.register(model)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        track = make_track()

        pipeline.process(frame, [track])
        assert track.attributes.get("smoking_prob") == 0.85

    def test_skips_non_person_tracks(self):
        registry = AttributeModelRegistry()
        model = MockModel()
        registry.register(model)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        car_track = make_track(class_name="car")

        pipeline.process(frame, [car_track])
        assert "mock_attr" not in car_track.attributes

    def test_multiple_models(self):
        registry = AttributeModelRegistry()
        m1 = MockModel("m1", result={"attr_a": 0.5})
        m2 = MockModel("m2", result={"attr_b": 0.7})
        registry.register(m1)
        registry.register(m2)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        track = make_track()

        pipeline.process(frame, [track])
        assert track.attributes.get("attr_a") == 0.5
        assert track.attributes.get("attr_b") == 0.7

    def test_multiple_tracks(self):
        registry = AttributeModelRegistry()
        model = MockModel(result={"test_val": 0.6})
        registry.register(model)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        t1 = make_track(track_id=1, bbox=(10, 10, 100, 100))
        t2 = make_track(track_id=2, bbox=(200, 200, 300, 300))

        pipeline.process(frame, [t1, t2])
        assert t1.attributes.get("test_val") == 0.6
        assert t2.attributes.get("test_val") == 0.6

    def test_invalid_bbox_skipped(self):
        registry = AttributeModelRegistry()
        model = MockModel()
        registry.register(model)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        # Invalid bbox: x2 <= x1
        track = make_track(bbox=(200, 200, 100, 100))

        pipeline.process(frame, [track])
        assert "mock_attr" not in track.attributes

    def test_no_models_noop(self):
        registry = AttributeModelRegistry()
        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()
        track = make_track()

        pipeline.process(frame, [track])
        assert len(track.attributes) == 0

    def test_empty_tracks_noop(self):
        registry = AttributeModelRegistry()
        model = MockModel()
        registry.register(model)

        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame()

        pipeline.process(frame, [])  # Should not raise
        assert model._infer_count == 0

    def test_crop_resize(self):
        """Verify crop is resized to standard size."""
        registry = AttributeModelRegistry()

        class SizeCheckModel(AttributeModel):
            @property
            def name(self):
                return "size_check"

            @property
            def target_classes(self):
                return ["person"]

            def load(self):
                pass

            def infer(self, crop):
                assert crop.shape == (224, 224, 3)
                return {"ok": 1.0}

            def unload(self):
                pass

        registry.register(SizeCheckModel())
        pipeline = CascadeAttributePipeline(registry)
        frame = make_frame(h=1080, w=1920)
        track = make_track(bbox=(100, 100, 500, 800))

        pipeline.process(frame, [track])
        assert track.attributes.get("ok") == 1.0
