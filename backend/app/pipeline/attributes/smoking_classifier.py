import gc
import logging
from pathlib import Path

import numpy as np

from app.pipeline.attributes.base import AttributeModel

logger = logging.getLogger(__name__)


class SmokingClassifier(AttributeModel):
    """
    CNN classifier for smoking detection on person crops.

    Uses a lightweight CNN (MobileNetV3-Small or similar).
    Falls back to a dummy model if weights are not available (for development).
    """

    @property
    def name(self) -> str:
        return "smoking"

    @property
    def target_classes(self) -> list[str]:
        return ["person"]

    def __init__(self, model_path: str | None = None, device: str = "cuda") -> None:
        self._model_path = model_path
        self._device = device
        self._model = None
        self._transform = None
        self._use_dummy = model_path is None or not Path(model_path).exists()

    def load(self) -> None:
        if self._use_dummy:
            logger.warning(
                "Smoking classifier: no model weights found, using dummy classifier"
            )
            return

        import torch
        import torchvision.transforms as T

        self._model = torch.jit.load(self._model_path, map_location=self._device)
        self._model.eval()
        self._transform = T.Compose([
            T.ToPILImage(),
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        logger.info("Smoking classifier loaded from %s", self._model_path)

    def infer(self, crop: np.ndarray) -> dict[str, float]:
        if self._use_dummy:
            return {"smoking_prob": 0.0}

        import torch

        tensor = self._transform(crop).unsqueeze(0).to(self._device)
        with torch.no_grad():
            output = self._model(tensor)
            prob = torch.sigmoid(output).item()
        return {"smoking_prob": round(prob, 4)}

    def infer_batch(self, crops: list[np.ndarray]) -> list[dict[str, float]]:
        if self._use_dummy:
            return [{"smoking_prob": 0.0} for _ in crops]

        import torch

        tensors = torch.stack([self._transform(c) for c in crops]).to(self._device)
        with torch.no_grad():
            outputs = self._model(tensors)
            probs = torch.sigmoid(outputs).squeeze(-1).cpu().tolist()
        if isinstance(probs, float):
            probs = [probs]
        return [{"smoking_prob": round(p, 4)} for p in probs]

    def unload(self) -> None:
        self._model = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
