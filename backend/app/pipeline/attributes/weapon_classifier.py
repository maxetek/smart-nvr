import gc
import logging
from pathlib import Path

import numpy as np

from app.pipeline.attributes.base import AttributeModel

logger = logging.getLogger(__name__)

WEAPON_CLASSES = ["pistol", "knife", "rifle", "none"]


class WeaponClassifier(AttributeModel):
    """
    CNN classifier for weapon detection on person crops.

    Multi-class output: pistol, knife, rifle, none.
    Falls back to a dummy model if weights are not available (for development).
    """

    @property
    def name(self) -> str:
        return "weapon"

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
                "Weapon classifier: no model weights found, using dummy classifier"
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
        logger.info("Weapon classifier loaded from %s", self._model_path)

    def _parse_output(self, probs: list[float]) -> dict[str, float]:
        """Parse model output into weapon probability and type."""
        # probs: [pistol, knife, rifle, none]
        none_idx = WEAPON_CLASSES.index("none")
        weapon_prob = 1.0 - probs[none_idx]
        best_idx = max(range(len(probs) - 1), key=lambda i: probs[i])
        weapon_type = WEAPON_CLASSES[best_idx] if weapon_prob > 0.5 else "none"
        return {
            "weapon_prob": round(weapon_prob, 4),
            "weapon_type": weapon_type,
        }

    def infer(self, crop: np.ndarray) -> dict[str, float]:
        if self._use_dummy:
            return {"weapon_prob": 0.0, "weapon_type": "none"}

        import torch

        tensor = self._transform(crop).unsqueeze(0).to(self._device)
        with torch.no_grad():
            output = self._model(tensor)
            probs = torch.softmax(output, dim=1).squeeze(0).cpu().tolist()
        return self._parse_output(probs)

    def infer_batch(self, crops: list[np.ndarray]) -> list[dict[str, float]]:
        if self._use_dummy:
            return [{"weapon_prob": 0.0, "weapon_type": "none"} for _ in crops]

        import torch

        tensors = torch.stack([self._transform(c) for c in crops]).to(self._device)
        with torch.no_grad():
            outputs = self._model(tensors)
            all_probs = torch.softmax(outputs, dim=1).cpu().tolist()
        return [self._parse_output(p) for p in all_probs]

    def unload(self) -> None:
        self._model = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
