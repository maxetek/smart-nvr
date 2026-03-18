import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraResponse, CameraUpdate
from app.schemas.pagination import PaginatedResponse
from app.services import camera_service

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])


@router.get("/", response_model=PaginatedResponse)
@limiter.limit("60/minute")
async def list_cameras(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    cameras, total = await camera_service.list_cameras(db, limit=limit, offset=offset)
    items = [CameraResponse.model_validate(c) for c in cameras]
    return PaginatedResponse(
        items=[i.model_dump() for i in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{camera_id}", response_model=CameraResponse)
@limiter.limit("60/minute")
async def get_camera(
    request: Request,
    camera_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CameraResponse:
    camera = await camera_service.get_camera(db, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return CameraResponse.model_validate(camera)


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_camera(
    request: Request,
    body: CameraCreate,
    current_user: User = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
) -> CameraResponse:
    camera = await camera_service.create_camera(db, body)
    return CameraResponse.model_validate(camera)


@router.put("/{camera_id}", response_model=CameraResponse)
@limiter.limit("60/minute")
async def update_camera(
    request: Request,
    camera_id: uuid.UUID,
    body: CameraUpdate,
    current_user: User = Depends(require_role("admin", "operator")),
    db: AsyncSession = Depends(get_db),
) -> CameraResponse:
    camera = await camera_service.update_camera(db, camera_id, body)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return CameraResponse.model_validate(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_camera(
    request: Request,
    camera_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await camera_service.delete_camera(db, camera_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
