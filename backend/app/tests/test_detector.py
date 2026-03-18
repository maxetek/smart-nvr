import numpy as np
import pytest

from app.pipeline.detector.yolo_detector import DetectorConfig, YOLODetector


class TestDetectorConfig:
    """Tests for DetectorConfig defaults."""

    def test_default_config_values(self):
        """Test that DetectorConfig has sensible defaults."""
        config = DetectorConfig()
        assert config.model_path == "yolov8n.pt"
        assert config.confidence_threshold == 0.25
        assert config.iou_threshold == 0.45
        assert config.device == "cuda"
        assert config.half is True
        assert config.img_size == 640
        assert config.classes is None
        assert config.max_det == 100

    def test_custom_config(self):
        """Test that DetectorConfig accepts custom values."""
        config = DetectorConfig(
            model_path="yolov8s.pt",
            confidence_threshold=0.5,
            device="cpu",
            half=False,
            classes=[0, 1, 2],
        )
        assert config.model_path == "yolov8s.pt"
        assert config.confidence_threshold == 0.5
        assert config.device == "cpu"
        assert config.half is False
        assert config.classes == [0, 1, 2]


class TestYOLODetector:
    """Tests for YOLODetector wrapper."""

    def test_detect_raises_without_load(self):
        """Test that detect() raises RuntimeError if model not loaded."""
        detector = YOLODetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect(frame)

    def test_detect_batch_raises_without_load(self):
        """Test that detect_batch() raises RuntimeError if model not loaded."""
        detector = YOLODetector()
        frames = [np.zeros((480, 640, 3), dtype=np.uint8)]

        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect_batch(frames)

    def test_class_names_empty_before_load(self):
        """Test that class_names is empty before model is loaded."""
        detector = YOLODetector()
        assert detector.class_names == {}

    def test_detector_accepts_config(self):
        """Test that YOLODetector accepts a custom config."""
        config = DetectorConfig(model_path="yolov8m.pt", device="cpu")
        detector = YOLODetector(config=config)
        assert detector.config.model_path == "yolov8m.pt"
        assert detector.config.device == "cpu"
