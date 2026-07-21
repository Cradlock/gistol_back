



from datetime import datetime
from typing import final

from sqlalchemy import Enum, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
from app.models.years import Year

@final
class SituationsTask(Base):
    __tablename__ = "situations_task" 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    duration_min: Mapped[int] = mapped_column()



@final
class StudentAnswerTask(Base):
    __tablename__ = "student_answer_task"
    
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task_id: Mapped[int] = mapped_column(ForeignKey("situations_task.id"))

    text: Mapped[str] = mapped_column(String(255))

@final 
class TaskTargets(Base):
    __tablename__ = "task_targets"
    

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("situations_task.id", ondelete="CASCADE"))

    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    year: Mapped[Year] = mapped_column(Enum(Year), nullable=True)




