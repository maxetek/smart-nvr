from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.pattern import Pattern


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cameras.id"), index=True)
    pattern_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("patterns.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # line_cross, zone_intrusion, smoking, weapon, loitering, crowd
    severity: Mapped[str] = mapped_column(
        String(20), default="info"
    )  # info, warning, critical
    confidence: Mapped[float] = mapped_column(default=0.0)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clip_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # track_id, bbox, zone_name, etc.
    is_acknowledged: Mapped[bool] = mapped_column(default=False)
    acknowledged_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

    # Relationships
    camera: Mapped[Camera] = relationship(back_populates="events")
    pattern: Mapped[Optional[Pattern]] = relationship(back_populates="events")
