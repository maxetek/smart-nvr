import logging
from dataclasses import dataclass

import numpy as np

from app.pipeline.models.detection import Detection

logger = logging.getLogger(__name__)


@dataclass
class DetectorConfig:
    """Configuration for the YOLO detector."""

    model_path: str = "yolov8n.pt"  # Default to nano for testing
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.45
    device: str = "cuda"  # "cuda", "cpu"
    half: bool = True  # FP16
    img_size: int = 640
    classes: list[int] | None = None  # Filter classes (e.g., [0] for person only)
    max_det: int = 100


class YOLODetector:
    """Wrapper around Ultralytics YOLO for inference."""

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config = config or DetectorConfig()
        self._model = None
        self._class_names: dict[int, str] = {}

    def load(self) -> None:
        """Load the YOLO model. Call once at startup."""
        from ultralytics import YOLO

        self._model = YOLO(self.config.model_path)
        # Move to device and set half precision
        if self.config.half and self.config.device == "cuda":
            self._model.to(self.config.device)
        self._class_names = self._model.names
        logger.info(
            "YOLO model loaded: %s on %s (FP16=%s)",
            self.config.model_path,
            self.config.device,
            self.config.half,
        )

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Run inference on a single frame. Returns list of Detection."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._model.predict(
            source=frame,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            device=self.config.device,
            half=self.config.half,
            imgsz=self.config.img_size,
            classes=self.config.classes,
            max_det=self.config.max_det,
            verbose=False,
        )

        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for i in range(len(boxes)):
                bbox = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu())
                cls_id = int(boxes.cls[i].cpu())
                cls_name = self._class_names.get(cls_id, f"class_{cls_id}")
                detections.append(
                    Detection(
                        bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
                        confidence=conf,
                        class_id=cls_id,
                        class_name=cls_name,
                    )
                )
        return detections

    def detect_batch(self, frames: list[np.ndarray]) -> list[list[Detection]]:
        """Run inference on a batch of frames."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        results = self._model.predict(
            source=frames,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            device=self.config.device,
            half=self.config.half,
            imgsz=self.config.img_size,
            classes=self.config.classes,
            max_det=self.config.max_det,
            verbose=False,
        )

        batch_detections: list[list[Detection]] = []
        for result in results:
            detections: list[Detection] = []
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    bbox = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu())
                    cls_id = int(boxes.cls[i].cpu())
                    cls_name = self._class_names.get(cls_id, f"class_{cls_id}")
                    detections.append(
                        Detection(
                            bbox=(
                                float(bbox[0]),
                                float(bbox[1]),
                                float(bbox[2]),
                                float(bbox[3]),
                            ),
                            confidence=conf,
                            class_id=cls_id,
                            class_name=cls_name,
                        )
                    )
            batch_detections.append(detections)
        return batch_detections

    @property
    def class_names(self) -> dict[int, str]:
        """Return the class name mapping from the loaded model."""
        return self._class_names
