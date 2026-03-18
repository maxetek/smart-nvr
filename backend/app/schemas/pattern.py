import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PatternCreate(BaseModel):
    camera_id: uuid.UUID
    name: str = Field(max_length=100)
    pattern_type: str = Field(max_length=50)
    config_json: dict
    cooldown_seconds: int = 60
    is_enabled: bool = True


class PatternUpdate(BaseModel):
    name: str | None = None
    config_json: dict | None = None
    cooldown_seconds: int | None = None
    is_enabled: bool | None = None


class PatternResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    name: str
    pattern_type: str
    is_enabled: bool
    config_json: dict
    cooldown_seconds: int
    last_triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
