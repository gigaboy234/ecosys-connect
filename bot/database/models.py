import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    student = "student"
    startup = "startup"
    teacher = "teacher"
    partner = "partner"


class StartupStage(str, enum.Enum):
    idea = "idea"
    mvp = "mvp"
    prototype = "prototype"
    scaling = "scaling"


class StudentGoal(str, enum.Enum):
    find_startup = "find_startup"
    create_startup = "create_startup"
    find_teacher = "find_teacher"


class TeacherFormat(str, enum.Enum):
    offline = "offline"
    online = "online"
    mixed = "mixed"


class RequestType(str, enum.Enum):
    join_startup = "join_startup"        # студент → стартап
    mentor_startup = "mentor_startup"    # преподаватель → стартап
    consult_student = "consult_student"  # студент → преподаватель
    partner_startup = "partner_startup"  # партнёр → стартап
    intern_search = "intern_search"      # партнёр → студент


class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


# ─── Core ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    role: Mapped[Optional[UserRole]] = mapped_column(Enum(UserRole), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    student: Mapped[Optional["Student"]] = relationship(back_populates="user", uselist=False)
    teacher: Mapped[Optional["Teacher"]] = relationship(back_populates="user", uselist=False)
    partner: Mapped[Optional["Partner"]] = relationship(back_populates="user", uselist=False)
    owned_startup: Mapped[Optional["Startup"]] = relationship(
        back_populates="captain", foreign_keys="Startup.captain_id", uselist=False
    )
    startup_memberships: Mapped[List["StartupMember"]] = relationship(back_populates="user")
    sent_requests: Mapped[List["Request"]] = relationship(
        back_populates="from_user", foreign_keys="Request.from_user_id"
    )
    reports_filed: Mapped[List["Report"]] = relationship(
        back_populates="reporter", foreign_keys="Report.reporter_id"
    )
    reports_received: Mapped[List["Report"]] = relationship(
        back_populates="reported", foreign_keys="Report.reported_id"
    )


# ─── Profiles ─────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    surname: Mapped[str] = mapped_column(String(64), nullable=False)
    university: Mapped[str] = mapped_column(String(128), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)          # курс 1-6
    faculty: Mapped[str] = mapped_column(String(128), nullable=False)

    # JSON-списки: ["IT", "Дизайн"], ["AI", "Web3"]
    directions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tech_interests: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    portfolio: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[StudentGoal] = mapped_column(Enum(StudentGoal), nullable=False)
    photo_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    user: Mapped["User"] = relationship(back_populates="student")


class Startup(Base):
    __tablename__ = "startups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    captain_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    stage: Mapped[StartupStage] = mapped_column(Enum(StartupStage), nullable=False)
    needs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contact: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    captain: Mapped["User"] = relationship(
        back_populates="owned_startup", foreign_keys=[captain_id]
    )
    members: Mapped[List["StartupMember"]] = relationship(back_populates="startup")
    requests: Mapped[List["Request"]] = relationship(back_populates="startup")


class StartupMember(Base):
    __tablename__ = "startup_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    startup_id: Mapped[int] = mapped_column(ForeignKey("startups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role_in_team: Mapped[str] = mapped_column(String(64), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    startup: Mapped["Startup"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="startup_memberships")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    degree: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    research_directions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    competencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    help_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    availability: Mapped[int] = mapped_column(Integer, nullable=False)  # часов в неделю
    format: Mapped[TeacherFormat] = mapped_column(Enum(TeacherFormat), nullable=False)
    photo_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    user: Mapped["User"] = relationship(back_populates="teacher")


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    sphere: Mapped[str] = mapped_column(String(128), nullable=False)
    needs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    resources: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contact_person: Mapped[str] = mapped_column(String(128), nullable=False)
    photo_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    user: Mapped["User"] = relationship(back_populates="partner")


# ─── Requests ─────────────────────────────────────────────────────────────────

class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    startup_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("startups.id"), nullable=True, index=True
    )
    # to_user_id используется для запросов студент→преподаватель и партнёр→студент
    to_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    request_type: Mapped[RequestType] = mapped_column(Enum(RequestType), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.pending, nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    from_user: Mapped["User"] = relationship(
        back_populates="sent_requests", foreign_keys=[from_user_id]
    )
    startup: Mapped[Optional["Startup"]] = relationship(back_populates="requests")


# ─── Reports ──────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reported_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    reporter: Mapped["User"] = relationship(
        back_populates="reports_filed", foreign_keys=[reporter_id]
    )
    reported: Mapped["User"] = relationship(
        back_populates="reports_received", foreign_keys=[reported_id]
    )
