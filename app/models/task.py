from datetime import datetime
import enum
from typing import final

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.groups import Group


class StudentAnswerStatus(str, enum.Enum):
    PENDING = "pending"
    POSITIVE = "positive"
    NEGATIVE = "negative"


@final
class SituationsTask(Base):
    __tablename__ = "situations_task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(4000))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    points: Mapped[int] = mapped_column()

    group: Mapped[Group] = relationship()
    answers: Mapped[list["StudentAnswerTask"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )


@final
class StudentAnswerTask(Base):
    __tablename__ = "student_answer_task"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_student_task_answer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[int] = mapped_column(
        ForeignKey("situations_task.id", ondelete="CASCADE")
    )
    text: Mapped[str] = mapped_column(String(255))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    status: Mapped[StudentAnswerStatus] = mapped_column(
        Enum(
            StudentAnswerStatus,
            name="student_answer_status",
            values_callable=lambda items: [item.value for item in items],
        ),
        default=StudentAnswerStatus.PENDING,
    )

    task: Mapped[SituationsTask] = relationship(back_populates="answers")
