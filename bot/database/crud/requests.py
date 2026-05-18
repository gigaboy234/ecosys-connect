from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Request, RequestStatus, RequestType


async def create_request(
    session: AsyncSession,
    from_user_id: int,
    request_type: RequestType,
    startup_id: Optional[int] = None,
    to_user_id: Optional[int] = None,
    message: Optional[str] = None,
) -> Request:
    req = Request(
        from_user_id=from_user_id,
        request_type=request_type,
        startup_id=startup_id,
        to_user_id=to_user_id,
        message=message,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def get_request_by_id(session: AsyncSession, request_id: int) -> Optional[Request]:
    result = await session.execute(
        select(Request)
        .where(Request.id == request_id)
        .options(selectinload(Request.from_user))
    )
    return result.scalar_one_or_none()


async def get_pending_for_startup(session: AsyncSession, startup_id: int) -> list[Request]:
    result = await session.execute(
        select(Request)
        .where(Request.startup_id == startup_id, Request.status == RequestStatus.pending)
        .options(selectinload(Request.from_user))
    )
    return result.scalars().all()


async def get_pending_for_user(session: AsyncSession, to_user_id: int) -> list[Request]:
    result = await session.execute(
        select(Request)
        .where(Request.to_user_id == to_user_id, Request.status == RequestStatus.pending)
        .options(selectinload(Request.from_user))
    )
    return result.scalars().all()


async def set_request_status(
    session: AsyncSession, request_id: int, status: RequestStatus
) -> Optional[Request]:
    req = await get_request_by_id(session, request_id)
    if not req:
        return None
    req.status = status
    await session.commit()
    await session.refresh(req)
    return req


async def has_pending_request(
    session: AsyncSession,
    from_user_id: int,
    request_type: RequestType,
    startup_id: Optional[int] = None,
    to_user_id: Optional[int] = None,
) -> bool:
    conditions = [
        Request.from_user_id == from_user_id,
        Request.request_type == request_type,
        Request.status == RequestStatus.pending,
    ]
    if startup_id:
        conditions.append(Request.startup_id == startup_id)
    if to_user_id:
        conditions.append(Request.to_user_id == to_user_id)

    result = await session.execute(select(Request).where(and_(*conditions)))
    return result.scalar_one_or_none() is not None
