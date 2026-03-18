from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_cameras: int
    active_cameras: int
    total_events_today: int
    unacknowledged_events: int
    events_by_type: dict[str, int]
    events_by_severity: dict[str, int]
    recent_events_count_1h: int
    pipeline_status: dict | None = None
