"""Moderation API routes"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.moderation import (
    ReportCreate,
    ReportResolve,
    ReportResponse,
    ReportListResponse,
    BanCreate,
    ReportStatus,
    ReportReason,
)
from src.core.dependencies import get_db, get_current_user, require_moderator
from src.models.user import User
from src.services.moderation_service import ModerationService

router = APIRouter()


@router.post(
    "/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a report",
)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Report content (post or comment) for moderation.

    **Required:**
    - Either `post_id` OR `comment_id` (not both)
    - `reason`: Spam, harassment, hate_speech, etc.

    **Optional:**
    - `description`: Additional details
    """
    moderation_service = ModerationService(db)
    report = await moderation_service.create_report(report_data, current_user.id)
    return report


@router.get("/reports", response_model=ReportListResponse, summary="List reports")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[ReportStatus] = Query(None),
    reason: Optional[ReportReason] = Query(None),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    List all reports (moderator only).

    **Filters:**
    - `status`: pending, reviewing, resolved, rejected
    - `reason`: spam, harassment, etc.
    """
    moderation_service = ModerationService(db)
    reports, total = await moderation_service.list_reports(
        page=page, page_size=page_size, status=status, reason=reason
    )

    total_pages = (total + page_size - 1) // page_size

    return ReportListResponse(
        reports=reports, total=total, page=page, page_size=page_size, total_pages=total_pages
    )


@router.get("/reports/{report_id}", response_model=ReportResponse, summary="Get report by ID")
async def get_report(
    report_id: int = Path(...),
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """Get report details (moderator only)."""
    moderation_service = ModerationService(db)
    report = await moderation_service.get_report_by_id(report_id)
    return report


@router.patch("/reports/{report_id}", response_model=ReportResponse, summary="Resolve a report")
async def resolve_report(
    report_id: int = Path(...),
    resolve_data: ReportResolve = ...,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve a report (moderator only).

    **Actions:**
    - `status`: resolved, rejected
    - `moderator_notes`: Internal notes
    - `resolution`: Action taken
    """
    moderation_service = ModerationService(db)
    report = await moderation_service.resolve_report(
        report_id=report_id, resolve_data=resolve_data, moderator_id=current_user.id
    )
    return report


@router.post("/ban", status_code=status.HTTP_204_NO_CONTENT, summary="Ban a user")
async def ban_user(
    ban_data: BanCreate,
    current_user: User = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
):
    """
    Ban a user (moderator only).

    **Required:**
    - `user_id`: User to ban
    - `reason`: Ban reason

    **Optional:**
    - `duration_days`: Ban duration (None = permanent)
    """
    moderation_service = ModerationService(db)
    await moderation_service.ban_user(
        user_id=ban_data.user_id,
        reason=ban_data.reason,
        duration_days=ban_data.duration_days,
        banned_by_id=current_user.id,
    )
    return None
