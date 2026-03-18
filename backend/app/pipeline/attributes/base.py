import abc

import numpy as np


class AttributeModel(abc.ABC):
    """Base class for attribute classifiers (smoking, weapon, etc.)."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique model name, e.g., 'smoking', 'weapon'."""
        ...

    @property
    @abc.abstractmethod
    def target_classes(self) -> list[str]:
        """Which object classes this applies to, e.g., ['person']."""
        ...

    @abc.abstractmethod
    def load(self) -> None:
        """Load model weights."""
        ...

    @abc.abstractmethod
    def infer(self, crop: np.ndarray) -> dict[str, float]:
        """
        Run inference on a single person crop.
        Returns dict of attribute probabilities, e.g.:
        {"smoking_prob": 0.92} or {"weapon_prob": 0.87, "weapon_type": "pistol"}
        """
        ...

    def infer_batch(self, crops: list[np.ndarray]) -> list[dict[str, float]]:
        """Batch inference. Default: sequential. Override for true batching."""
        return [self.infer(crop) for crop in crops]

    @abc.abstractmethod
    def unload(self) -> None:
        """Release model from memory."""
        ...
