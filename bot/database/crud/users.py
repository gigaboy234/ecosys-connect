from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, UserRole


async def get_user_by_tg_id(session: AsyncSession, tg_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, tg_id: int, username: Optional[str]) -> User:
    user = User(tg_id=tg_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(
    session: AsyncSession, tg_id: int, username: Optional[str]
) -> tuple[User, bool]:
    user = await get_user_by_tg_id(session, tg_id)
    if user:
        return user, False
    user = await create_user(session, tg_id, username)
    return user, True


async def set_user_role(session: AsyncSession, tg_id: int, role: UserRole) -> User:
    user = await get_user_by_tg_id(session, tg_id)
    user.role = role
    await session.commit()
    await session.refresh(user)
    return user


async def ban_user(session: AsyncSession, user_id: int) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_banned = True
        await session.commit()


async def unban_user(session: AsyncSession, user_id: int) -> None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_banned = False
        await session.commit()
