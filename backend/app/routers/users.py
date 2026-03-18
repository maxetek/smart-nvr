import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserResponse, UserRoleUpdate
from app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=PaginatedResponse)
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    users, total = await user_service.list_users(db, limit=limit, offset=offset)
    items = [UserResponse.model_validate(u) for u in users]
    return PaginatedResponse(
        items=[i.model_dump() for i in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/{user_id}/role", response_model=UserResponse)
@limiter.limit("60/minute")
async def update_user_role(
    request: Request,
    user_id: uuid.UUID,
    body: UserRoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    if body.role not in ("admin", "operator", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be admin, operator, or viewer.",
        )
    user = await user_service.update_user_role(db, user_id, body.role)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )
    user = await user_service.deactivate_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
