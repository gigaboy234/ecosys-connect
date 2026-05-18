from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Report


async def create_report(
    session: AsyncSession, reporter_id: int, reported_id: int, reason: str
) -> Report:
    report = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason)
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def get_unreviewed_reports(session: AsyncSession) -> list[Report]:
    result = await session.execute(
        select(Report)
        .where(Report.is_reviewed == False)
        .options(selectinload(Report.reporter), selectinload(Report.reported))
        .order_by(Report.created_at)
    )
    return result.scalars().all()


async def mark_reviewed(session: AsyncSession, report_id: int) -> None:
    result = await session.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report:
        report.is_reviewed = True
        await session.commit()
