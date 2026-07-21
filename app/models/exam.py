from datetime import datetime
import enum
from typing import final

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Enum, Uuid
from app.models.base import Base

from sqlalchemy.dialects.postgresql import JSONB

# ================== Админ часть

@final
class Exam(Base):
    __tablename__ = "exams"
    """
    Таблица для ЭКЗАМЕНОВ - НЕ ситуационные 
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250)) # Название 
    theme: Mapped[str] = mapped_column(String(500)) # Тема
    

    # начало                       
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # длительность в МИНУТАХ ебАТЬ
    duration_minutes: Mapped[int] = mapped_column(default=1)


@final 
class ExamTargets(Base):
    __tablename__ = "exam_targets"
    

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))

    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    year_id: Mapped[int | None] = mapped_column(ForeignKey("years.id"), nullable=True)


@final 
class QuestionType(enum.Enum):
    CHOISE = "choise"
    INPUT = "input"


@final 
class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    # Это сам вопрос 
    text: Mapped[str] = mapped_column(String(1000))
    # Тип вопроса 
    type: Mapped[QuestionType] = mapped_column()
    

@final 
class Choice(Base):
    __tablename__ = "choices"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(default=False)
    
    # Специальный аргумент для БД(для настроек таблицы)
    __table_args__ : tuple[Index] = (Index(
        "uq_choice_is_correct",                 # Просто тех.имя   
        "question_id",                          # Используемое поле для выборки  
        unique=True,                            # Проверка уникальности для ответов 
        postgresql_where=(is_correct == True)), # Фильтр (тольок is_correct = True) проходят
    )

    

@final 
class Input(Base):
    __tablename__ = "inputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String(255))







# ============== Студент часть

class ExamSessionStatus(enum.Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


@final 
class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    status: Mapped[ExamSessionStatus] = mapped_column() 
    started_at: Mapped[datetime] = mapped_column()

    answers: Mapped[dict | list] = mapped_column(JSONB, nullable=True, default=dict)







