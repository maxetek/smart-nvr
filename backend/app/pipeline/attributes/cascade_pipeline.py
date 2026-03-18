import logging

import cv2
import numpy as np

from app.pipeline.attributes.registry import AttributeModelRegistry
from app.pipeline.models.track import Track

logger = logging.getLogger(__name__)


class CascadeAttributePipeline:
    """
    Cascade: for each tracked person, crop the image, run through
    all registered attribute models, store results in track.attributes.

    Optimized: batch crops per model for GPU efficiency.
    """

    def __init__(self, registry: AttributeModelRegistry) -> None:
        self.registry = registry
        self._crop_size: tuple[int, int] = (224, 224)  # Standard input size

    def process(self, frame: np.ndarray, tracks: list[Track]) -> None:
        """Run all attribute models on person tracks."""
        # 1. Filter person tracks
        person_tracks = [t for t in tracks if t.class_name == "person"]
        if not person_tracks:
            return

        # 2. Get models for "person" class
        models = self.registry.get_for_class("person")
        if not models:
            return

        # 3. Batch crop all persons
        crops: list[np.ndarray] = []
        valid_tracks: list[Track] = []
        for track in person_tracks:
            crop = self._crop_person(frame, track)
            if crop is not None:
                crops.append(crop)
                valid_tracks.append(track)

        if not crops:
            return

        # 4. Run each model on the batch
        for model in models:
            try:
                results = model.infer_batch(crops)
                for track, attrs in zip(valid_tracks, results):
                    track.attributes.update(attrs)
            except Exception as e:
                logger.error("Attribute model '%s' failed: %s", model.name, e)

    def _crop_person(self, frame: np.ndarray, track: Track) -> np.ndarray | None:
        """Crop and resize person from frame."""
        h, w = frame.shape[:2]
        x1 = max(0, int(track.bbox[0]))
        y1 = max(0, int(track.bbox[1]))
        x2 = min(w, int(track.bbox[2]))
        y2 = min(h, int(track.bbox[3]))

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        crop = cv2.resize(crop, self._crop_size)
        return crop
