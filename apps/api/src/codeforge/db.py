from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from codeforge.config import settings


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    sandbox_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sandbox_state: Mapped[str] = mapped_column(String, default="running")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    messages: Mapped[List["MessageRow"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class MessageRow(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[object] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    session: Mapped["SessionRow"] = relationship(back_populates="messages")


engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_session(db: AsyncSession, title: str) -> SessionRow:
    row = SessionRow(id=str(uuid.uuid4()), title=title)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_session(db: AsyncSession, session_id: str) -> Optional[SessionRow]:
    result = await db.execute(select(SessionRow).where(SessionRow.id == session_id))
    return result.scalar_one_or_none()


async def update_sandbox_id(db: AsyncSession, session_id: str, sandbox_id: str) -> None:
    row = await get_session(db, session_id)
    if row:
        row.sandbox_id = sandbox_id
        row.sandbox_state = "running"
        await db.commit()


async def list_sessions(db: AsyncSession, *, limit: int = 50) -> List[SessionRow]:
    result = await db.execute(
        select(SessionRow).order_by(SessionRow.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def list_messages(db: AsyncSession, session_id: str) -> List[MessageRow]:
    result = await db.execute(
        select(MessageRow)
        .where(MessageRow.session_id == session_id)
        .order_by(MessageRow.created_at)
    )
    return list(result.scalars().all())


async def add_message(db: AsyncSession, session_id: str, role: str, content: object) -> MessageRow:
    row = MessageRow(id=str(uuid.uuid4()), session_id=session_id, role=role, content=content)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
