from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Detection:
    """Single object detection from a frame."""

    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2) absolute pixels
    confidence: float
    class_id: int
    class_name: str

    @property
    def center(self) -> tuple[float, float]:
        """Return the center point of the bounding box."""
        return ((self.bbox[0] + self.bbox[2]) / 2, (self.bbox[1] + self.bbox[3]) / 2)

    @property
    def area(self) -> float:
        """Return the area of the bounding box in pixels."""
        return (self.bbox[2] - self.bbox[0]) * (self.bbox[3] - self.bbox[1])
