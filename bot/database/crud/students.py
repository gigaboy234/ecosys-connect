from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Student, User


async def create_student(session: AsyncSession, user_id: int, data: dict) -> Student:
    student = Student(user_id=user_id, **data)
    session.add(student)
    await session.commit()
    await session.refresh(student)
    return student


async def get_student_by_user_id(session: AsyncSession, user_id: int) -> Optional[Student]:
    result = await session.execute(select(Student).where(Student.user_id == user_id))
    return result.scalar_one_or_none()


async def update_student(session: AsyncSession, user_id: int, data: dict) -> Optional[Student]:
    student = await get_student_by_user_id(session, user_id)
    if not student:
        return None
    for key, value in data.items():
        setattr(student, key, value)
    await session.commit()
    await session.refresh(student)
    return student


async def search_students(
    session: AsyncSession,
    directions: Optional[list] = None,
    exclude_user_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 5,
) -> list[Student]:
    stmt = select(Student).join(User).where(User.is_banned == False)
    if exclude_user_id:
        stmt = stmt.where(Student.user_id != exclude_user_id)

    students = (await session.execute(stmt)).scalars().all()

    if directions:
        students = [s for s in students if any(d in s.directions for d in directions)]

    return list(students[offset: offset + limit])
