from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
@limiter.limit("60/minute")
async def get_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    pipeline_manager = getattr(request.app.state, "pipeline_manager", None)
    return await dashboard_service.get_dashboard_summary(db, pipeline_manager)
