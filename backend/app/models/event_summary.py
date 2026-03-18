import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EventSummary(Base):
    __tablename__ = "event_summaries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cameras.id"), index=True)
    period_start: Mapped[datetime] = mapped_column(index=True)
    period_end: Mapped[datetime] = mapped_column()
    period_type: Mapped[str] = mapped_column(String(20))  # "minute", "hour", "day"
    total_detections: Mapped[int] = mapped_column(default=0)
    person_count: Mapped[int] = mapped_column(default=0)
    vehicle_count: Mapped[int] = mapped_column(default=0)
    max_concurrent_persons: Mapped[int] = mapped_column(default=0)
    event_counts_json: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"line_cross": 5, "smoking": 1}
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
