from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.camera import Camera
    from app.models.event import Event


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    camera_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cameras.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    pattern_type: Mapped[str] = mapped_column(
        String(50)
    )  # line_cross, zone_intrusion, loitering, smoking, weapon, crowd
    is_enabled: Mapped[bool] = mapped_column(default=True)
    config_json: Mapped[dict] = mapped_column(
        JSON
    )  # Stores: coordinates, thresholds, cooldowns, zones, confidence settings
    cooldown_seconds: Mapped[int] = mapped_column(default=60)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    camera: Mapped[Camera] = relationship(back_populates="patterns")
    events: Mapped[list[Event]] = relationship(back_populates="pattern")
