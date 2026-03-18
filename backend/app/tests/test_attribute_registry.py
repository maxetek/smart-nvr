import numpy as np

from app.pipeline.attributes.base import AttributeModel
from app.pipeline.attributes.registry import AttributeModelRegistry
from app.pipeline.attributes.smoking_classifier import SmokingClassifier
from app.pipeline.attributes.weapon_classifier import WeaponClassifier


class DummyModel(AttributeModel):
    """Simple model for testing the registry."""

    def __init__(self, name_val="test_model", classes=None):
        self._name = name_val
        self._classes = classes or ["person"]
        self._loaded = False

    @property
    def name(self):
        return self._name

    @property
    def target_classes(self):
        return self._classes

    def load(self):
        self._loaded = True

    def infer(self, crop):
        return {"test_attr": 0.5}

    def unload(self):
        self._loaded = False


class TestAttributeModelRegistry:
    def test_register(self):
        registry = AttributeModelRegistry()
        model = DummyModel()
        registry.register(model)

        assert "test_model" in registry.all_models
        assert model._loaded is True

    def test_unregister(self):
        registry = AttributeModelRegistry()
        model = DummyModel()
        registry.register(model)
        registry.unregister("test_model")

        assert "test_model" not in registry.all_models
        assert model._loaded is False

    def test_get(self):
        registry = AttributeModelRegistry()
        model = DummyModel()
        registry.register(model)

        assert registry.get("test_model") is model
        assert registry.get("nonexistent") is None

    def test_get_for_class(self):
        registry = AttributeModelRegistry()
        m1 = DummyModel("m1", ["person"])
        m2 = DummyModel("m2", ["vehicle"])
        m3 = DummyModel("m3", ["person", "vehicle"])
        registry.register(m1)
        registry.register(m2)
        registry.register(m3)

        person_models = registry.get_for_class("person")
        assert len(person_models) == 2
        assert m1 in person_models
        assert m3 in person_models

        vehicle_models = registry.get_for_class("vehicle")
        assert len(vehicle_models) == 2
        assert m2 in vehicle_models
        assert m3 in vehicle_models

    def test_unload_all(self):
        registry = AttributeModelRegistry()
        m1 = DummyModel("m1")
        m2 = DummyModel("m2")
        registry.register(m1)
        registry.register(m2)

        registry.unload_all()
        assert len(registry.all_models) == 0
        assert m1._loaded is False
        assert m2._loaded is False


class TestSmokingClassifierDummy:
    def test_dummy_mode(self):
        clf = SmokingClassifier(model_path=None)
        clf.load()
        result = clf.infer(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result == {"smoking_prob": 0.0}

    def test_dummy_batch(self):
        clf = SmokingClassifier(model_path=None)
        clf.load()
        crops = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(3)]
        results = clf.infer_batch(crops)
        assert len(results) == 3
        assert all(r["smoking_prob"] == 0.0 for r in results)

    def test_properties(self):
        clf = SmokingClassifier()
        assert clf.name == "smoking"
        assert clf.target_classes == ["person"]

    def test_unload(self):
        clf = SmokingClassifier()
        clf.load()
        clf.unload()  # Should not raise


class TestWeaponClassifierDummy:
    def test_dummy_mode(self):
        clf = WeaponClassifier(model_path=None)
        clf.load()
        result = clf.infer(np.zeros((224, 224, 3), dtype=np.uint8))
        assert result == {"weapon_prob": 0.0, "weapon_type": "none"}

    def test_dummy_batch(self):
        clf = WeaponClassifier(model_path=None)
        clf.load()
        crops = [np.zeros((224, 224, 3), dtype=np.uint8) for _ in range(3)]
        results = clf.infer_batch(crops)
        assert len(results) == 3
        assert all(r["weapon_prob"] == 0.0 for r in results)
        assert all(r["weapon_type"] == "none" for r in results)

    def test_properties(self):
        clf = WeaponClassifier()
        assert clf.name == "weapon"
        assert clf.target_classes == ["person"]

    def test_unload(self):
        clf = WeaponClassifier()
        clf.load()
        clf.unload()
