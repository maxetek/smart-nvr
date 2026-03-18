import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.pattern import PatternCreate, PatternResponse, PatternUpdate
from app.services import pattern_service

router = APIRouter(prefix="/api/v1/patterns", tags=["patterns"])


@router.get("/", response_model=PaginatedResponse)
@limiter.limit("60/minute")
async def list_patterns(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    camera_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    patterns, total = await pattern_service.list_patterns(
        db, camera_id=camera_id, limit=limit, offset=offset
    )
    items = [PatternResponse.model_validate(p) for p in patterns]
    return PaginatedResponse(
        items=[i.model_dump() for i in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{pattern_id}", response_model=PatternResponse)
@limiter.limit("60/minute")
async def get_pattern(
    request: Request,
    pattern_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatternResponse:
    pattern = await pattern_service.get_pattern(db, pattern_id)
    if pattern is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    return PatternResponse.model_validate(pattern)


@router.post("/", response_model=PatternResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_pattern(
    request: Request,
    body: PatternCreate,
    current_user: User = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
) -> PatternResponse:
    pattern = await pattern_service.create_pattern(db, body)
    return PatternResponse.model_validate(pattern)


@router.put("/{pattern_id}", response_model=PatternResponse)
@limiter.limit("60/minute")
async def update_pattern(
    request: Request,
    pattern_id: uuid.UUID,
    body: PatternUpdate,
    current_user: User = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
) -> PatternResponse:
    pattern = await pattern_service.update_pattern(db, pattern_id, body)
    if pattern is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
    return PatternResponse.model_validate(pattern)


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_pattern(
    request: Request,
    pattern_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await pattern_service.delete_pattern(db, pattern_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pattern not found")
