from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import Startup, StartupMember, User


async def create_startup(session: AsyncSession, captain_id: int, data: dict) -> Startup:
    startup = Startup(captain_id=captain_id, **data)
    session.add(startup)
    await session.commit()
    await session.refresh(startup)
    return startup


async def get_startup_by_id(session: AsyncSession, startup_id: int) -> Optional[Startup]:
    result = await session.execute(
        select(Startup)
        .where(Startup.id == startup_id)
        .options(selectinload(Startup.members).selectinload(StartupMember.user))
    )
    return result.scalar_one_or_none()


async def get_startup_by_captain(session: AsyncSession, captain_id: int) -> Optional[Startup]:
    result = await session.execute(
        select(Startup).where(Startup.captain_id == captain_id, Startup.is_active == True)
    )
    return result.scalar_one_or_none()


async def update_startup(session: AsyncSession, startup_id: int, data: dict) -> Optional[Startup]:
    startup = await get_startup_by_id(session, startup_id)
    if not startup:
        return None
    for key, value in data.items():
        setattr(startup, key, value)
    await session.commit()
    await session.refresh(startup)
    return startup


async def search_startups(
    session: AsyncSession,
    tags: Optional[list] = None,
    stage: Optional[str] = None,
    exclude_captain_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 5,
) -> list[Startup]:
    stmt = select(Startup).where(Startup.is_active == True)
    if stage:
        stmt = stmt.where(Startup.stage == stage)
    if exclude_captain_id:
        stmt = stmt.where(Startup.captain_id != exclude_captain_id)

    startups = (await session.execute(stmt)).scalars().all()

    if tags:
        startups = [s for s in startups if any(t in s.tags for t in tags)]

    return list(startups[offset: offset + limit])


async def add_member(
    session: AsyncSession, startup_id: int, user_id: int, role_in_team: str
) -> StartupMember:
    member = StartupMember(startup_id=startup_id, user_id=user_id, role_in_team=role_in_team)
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def remove_member(session: AsyncSession, startup_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(StartupMember).where(
            StartupMember.startup_id == startup_id,
            StartupMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return False
    await session.delete(member)
    await session.commit()
    return True


async def is_member(session: AsyncSession, startup_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(StartupMember).where(
            StartupMember.startup_id == startup_id,
            StartupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None
