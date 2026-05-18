from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Teacher, User


async def create_teacher(session: AsyncSession, user_id: int, data: dict) -> Teacher:
    teacher = Teacher(user_id=user_id, **data)
    session.add(teacher)
    await session.commit()
    await session.refresh(teacher)
    return teacher


async def get_teacher_by_user_id(session: AsyncSession, user_id: int) -> Optional[Teacher]:
    result = await session.execute(select(Teacher).where(Teacher.user_id == user_id))
    return result.scalar_one_or_none()


async def update_teacher(session: AsyncSession, user_id: int, data: dict) -> Optional[Teacher]:
    teacher = await get_teacher_by_user_id(session, user_id)
    if not teacher:
        return None
    for key, value in data.items():
        setattr(teacher, key, value)
    await session.commit()
    await session.refresh(teacher)
    return teacher


async def search_teachers(
    session: AsyncSession,
    directions: Optional[list] = None,
    offset: int = 0,
    limit: int = 5,
) -> list[Teacher]:
    stmt = select(Teacher).join(User).where(User.is_banned == False)
    teachers = (await session.execute(stmt)).scalars().all()

    if directions:
        teachers = [t for t in teachers if any(d in t.research_directions for d in directions)]

    return list(teachers[offset: offset + limit])
