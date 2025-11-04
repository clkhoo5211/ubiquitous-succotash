"""Moderation service"""

from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.moderation import Report, ReportStatus, ReportReason
from src.models.user import User
from src.schemas.moderation import ReportCreate, ReportResolve
from src.core.exceptions import ValidationError


class ModerationService:
    """Service for moderation operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        report_data: ReportCreate,
        reporter_id: int
    ) -> Report:
        """Create a content report"""
        # Validate that at least one target is specified
        if not report_data.post_id and not report_data.comment_id:
            raise ValidationError("Must specify either post_id or comment_id")

        if report_data.post_id and report_data.comment_id:
            raise ValidationError("Cannot report both post and comment simultaneously")

        report = Report(
            reporter_id=reporter_id,
            post_id=report_data.post_id,
            comment_id=report_data.comment_id,
            reason=report_data.reason,
            description=report_data.description,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow()
        )

        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)

        return report

    async def get_report_by_id(self, report_id: int) -> Report:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise ValidationError(f"Report with ID {report_id} not found")
        return report

    async def list_reports(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[ReportStatus] = None,
        reason: Optional[ReportReason] = None
    ) -> Tuple[List[Report], int]:
        """List reports with filters"""
        query = select(Report)

        if status:
            query = query.where(Report.status == status)
        if reason:
            query = query.where(Report.reason == reason)

        # Count
        count_query = select(func.count()).select_from(Report)
        if status:
            count_query = count_query.where(Report.status == status)
        if reason:
            count_query = count_query.where(Report.reason == reason)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Sort by created_at desc
        query = query.order_by(desc(Report.created_at))

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        reports = result.scalars().all()

        return list(reports), total

    async def resolve_report(
        self,
        report_id: int,
        resolve_data: ReportResolve,
        moderator_id: int
    ) -> Report:
        """Resolve a report"""
        report = await self.get_report_by_id(report_id)

        report.status = resolve_data.status
        report.moderator_notes = resolve_data.moderator_notes
        report.resolution = resolve_data.resolution
        report.reviewed_by_id = moderator_id
        report.reviewed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(report)

        return report

    async def ban_user(
        self,
        user_id: int,
        reason: str,
        duration_days: Optional[int],
        banned_by_id: int
    ) -> User:
        """Ban a user (placeholder - needs Ban model)"""
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValidationError(f"User with ID {user_id} not found")

        # For now, just deactivate the user
        # TODO: Create Ban model with expiration
        user.is_active = False
        await self.db.commit()

        return user
