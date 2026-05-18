from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Partner, User


async def create_partner(session: AsyncSession, user_id: int, data: dict) -> Partner:
    partner = Partner(user_id=user_id, **data)
    session.add(partner)
    await session.commit()
    await session.refresh(partner)
    return partner


async def get_partner_by_user_id(session: AsyncSession, user_id: int) -> Optional[Partner]:
    result = await session.execute(select(Partner).where(Partner.user_id == user_id))
    return result.scalar_one_or_none()


async def update_partner(session: AsyncSession, user_id: int, data: dict) -> Optional[Partner]:
    partner = await get_partner_by_user_id(session, user_id)
    if not partner:
        return None
    for key, value in data.items():
        setattr(partner, key, value)
    await session.commit()
    await session.refresh(partner)
    return partner


async def search_partners(
    session: AsyncSession,
    sphere: Optional[str] = None,
    offset: int = 0,
    limit: int = 5,
) -> list[Partner]:
    stmt = select(Partner).join(User).where(User.is_banned == False)
    if sphere:
        stmt = stmt.where(Partner.sphere == sphere)
    result = await session.execute(stmt.offset(offset).limit(limit))
    return result.scalars().all()
