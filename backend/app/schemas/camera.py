import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    name: str = Field(max_length=100)
    rtsp_url: str
    sub_stream_url: str | None = None
    location: str | None = None
    width: int | None = None
    height: int | None = None
    fps: int | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    rtsp_url: str | None = None
    sub_stream_url: str | None = None
    location: str | None = None
    is_enabled: bool | None = None
    width: int | None = None
    height: int | None = None
    fps: int | None = None


class CameraResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_enabled: bool
    location: str | None
    width: int | None
    height: int | None
    fps: int | None
    created_at: datetime
    updated_at: datetime
    # NOTE: Never expose rtsp_url in response!

    model_config = {"from_attributes": True}


class CameraDetailResponse(CameraResponse):
    """Extended response for admin users — shows relationship counts."""

    event_count: int = 0
    pattern_count: int = 0
