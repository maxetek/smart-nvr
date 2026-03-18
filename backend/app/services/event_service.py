import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.event import Event
from app.schemas.event import EventListParams


async def list_events(
    db: AsyncSession,
    filters: EventListParams,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    base_query = select(Event, Camera.name.label("camera_name")).outerjoin(
        Camera, Event.camera_id == Camera.id
    )

    count_query = select(func.count()).select_from(Event)

    if filters.camera_id is not None:
        base_query = base_query.where(Event.camera_id == filters.camera_id)
        count_query = count_query.where(Event.camera_id == filters.camera_id)
    if filters.event_type is not None:
        base_query = base_query.where(Event.event_type == filters.event_type)
        count_query = count_query.where(Event.event_type == filters.event_type)
    if filters.severity is not None:
        base_query = base_query.where(Event.severity == filters.severity)
        count_query = count_query.where(Event.severity == filters.severity)
    if filters.start_date is not None:
        base_query = base_query.where(Event.created_at >= filters.start_date)
        count_query = count_query.where(Event.created_at >= filters.start_date)
    if filters.end_date is not None:
        base_query = base_query.where(Event.created_at <= filters.end_date)
        count_query = count_query.where(Event.created_at <= filters.end_date)
    if filters.is_acknowledged is not None:
        base_query = base_query.where(Event.is_acknowledged == filters.is_acknowledged)
        count_query = count_query.where(Event.is_acknowledged == filters.is_acknowledged)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    result = await db.execute(
        base_query.order_by(Event.created_at.desc()).limit(limit).offset(offset)
    )
    rows = result.all()

    events = []
    for event, camera_name in rows:
        event_dict = {
            "id": event.id,
            "camera_id": event.camera_id,
            "camera_name": camera_name,
            "event_type": event.event_type,
            "severity": event.severity,
            "confidence": event.confidence,
            "thumbnail_path": event.thumbnail_path,
            "clip_path": event.clip_path,
            "metadata_json": event.metadata_json,
            "is_acknowledged": event.is_acknowledged,
            "acknowledged_by": event.acknowledged_by,
            "acknowledged_at": event.acknowledged_at,
            "created_at": event.created_at,
        }
        events.append(event_dict)
    return events, total


async def get_event(db: AsyncSession, event_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        select(Event, Camera.name.label("camera_name"))
        .outerjoin(Camera, Event.camera_id == Camera.id)
        .where(Event.id == event_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    event, camera_name = row
    return {
        "id": event.id,
        "camera_id": event.camera_id,
        "camera_name": camera_name,
        "event_type": event.event_type,
        "severity": event.severity,
        "confidence": event.confidence,
        "thumbnail_path": event.thumbnail_path,
        "clip_path": event.clip_path,
        "metadata_json": event.metadata_json,
        "is_acknowledged": event.is_acknowledged,
        "acknowledged_by": event.acknowledged_by,
        "acknowledged_at": event.acknowledged_at,
        "created_at": event.created_at,
    }


async def acknowledge_events(
    db: AsyncSession, event_ids: list[uuid.UUID], user_id: uuid.UUID
) -> int:
    now = datetime.now(timezone.utc)
    count = 0
    for eid in event_ids:
        event = await db.get(Event, eid)
        if event and not event.is_acknowledged:
            event.is_acknowledged = True
            event.acknowledged_by = user_id
            event.acknowledged_at = now
            count += 1
    await db.flush()
    return count


async def get_event_stats(db: AsyncSession) -> dict:
    type_result = await db.execute(
        select(Event.event_type, func.count()).group_by(Event.event_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    severity_result = await db.execute(
        select(Event.severity, func.count()).group_by(Event.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_result.all()}

    return {"by_type": by_type, "by_severity": by_severity}
