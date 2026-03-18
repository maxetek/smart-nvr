from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.event import Event
from app.schemas.dashboard import DashboardResponse


async def get_dashboard_summary(
    db: AsyncSession, pipeline_manager=None
) -> DashboardResponse:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    # Camera counts
    total_cameras_result = await db.execute(select(func.count()).select_from(Camera))
    total_cameras = total_cameras_result.scalar_one()

    active_cameras_result = await db.execute(
        select(func.count()).select_from(Camera).where(Camera.is_enabled.is_(True))
    )
    active_cameras = active_cameras_result.scalar_one()

    # Events today
    events_today_result = await db.execute(
        select(func.count())
        .select_from(Event)
        .where(Event.created_at >= today_start)
    )
    total_events_today = events_today_result.scalar_one()

    # Unacknowledged events
    unack_result = await db.execute(
        select(func.count())
        .select_from(Event)
        .where(Event.is_acknowledged.is_(False))
    )
    unacknowledged_events = unack_result.scalar_one()

    # Events by type
    type_result = await db.execute(
        select(Event.event_type, func.count())
        .where(Event.created_at >= today_start)
        .group_by(Event.event_type)
    )
    events_by_type = {row[0]: row[1] for row in type_result.all()}

    # Events by severity
    severity_result = await db.execute(
        select(Event.severity, func.count())
        .where(Event.created_at >= today_start)
        .group_by(Event.severity)
    )
    events_by_severity = {row[0]: row[1] for row in severity_result.all()}

    # Recent events (last hour)
    recent_result = await db.execute(
        select(func.count())
        .select_from(Event)
        .where(Event.created_at >= one_hour_ago)
    )
    recent_events_count_1h = recent_result.scalar_one()

    # Pipeline status
    pipeline_status = None
    if pipeline_manager is not None:
        try:
            pipeline_status = pipeline_manager.get_status()
        except Exception:
            pass

    return DashboardResponse(
        total_cameras=total_cameras,
        active_cameras=active_cameras,
        total_events_today=total_events_today,
        unacknowledged_events=unacknowledged_events,
        events_by_type=events_by_type,
        events_by_severity=events_by_severity,
        recent_events_count_1h=recent_events_count_1h,
        pipeline_status=pipeline_status,
    )
