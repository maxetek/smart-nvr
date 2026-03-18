import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.event import AcknowledgeRequest, EventListParams, EventResponse
from app.schemas.pagination import PaginatedResponse
from app.services import event_service

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("/", response_model=PaginatedResponse)
@limiter.limit("60/minute")
async def list_events(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    camera_id: uuid.UUID | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    is_acknowledged: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    filters = EventListParams(
        camera_id=camera_id,
        event_type=event_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        is_acknowledged=is_acknowledged,
    )
    events, total = await event_service.list_events(db, filters, limit=limit, offset=offset)
    return PaginatedResponse(
        items=events,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{event_id}", response_model=EventResponse)
@limiter.limit("60/minute")
async def get_event(
    request: Request,
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    event = await event_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventResponse(**event)


@router.post("/acknowledge", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def acknowledge_events(
    request: Request,
    body: AcknowledgeRequest,
    current_user: User = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    count = await event_service.acknowledge_events(db, body.event_ids, current_user.id)
    return {"acknowledged": count}
