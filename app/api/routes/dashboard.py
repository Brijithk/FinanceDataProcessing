from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import build_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_active_user)],
    recent_limit: Annotated[int, Query(ge=1, le=50)] = 10,
    trend_months: Annotated[int, Query(ge=1, le=36)] = 12,
) -> DashboardSummary:
    return await build_dashboard_summary(db, recent_limit=recent_limit, trend_months=trend_months)
