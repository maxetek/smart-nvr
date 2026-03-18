import uuid
from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    camera_name: str | None = None
    event_type: str
    severity: str
    confidence: float
    thumbnail_path: str | None
    clip_path: str | None
    metadata_json: dict | None
    is_acknowledged: bool
    acknowledged_by: uuid.UUID | None
    acknowledged_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListParams(BaseModel):
    camera_id: uuid.UUID | None = None
    event_type: str | None = None
    severity: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_acknowledged: bool | None = None


class AcknowledgeRequest(BaseModel):
    event_ids: list[uuid.UUID]
