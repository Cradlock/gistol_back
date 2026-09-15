from datetime import datetime
import enum
from typing import final

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.years import Year

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

    targets: Mapped[list["ExamTargets"]] = relationship(
        back_populates="exam", cascade="all, delete-orphan", passive_deletes=True
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Question.position",
    )
    sessions: Mapped[list["ExamSession"]] = relationship(
        back_populates="exam", cascade="all, delete-orphan", passive_deletes=True
    )


@final 
class ExamTargets(Base):
    __tablename__ = "exam_targets"
    

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"), nullable=True
    )
    year: Mapped[Year] = mapped_column(Enum(Year))

    exam: Mapped["Exam"] = relationship(back_populates="targets")
    group: Mapped["Group | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("exam_id", "group_id", "year", name="uq_exam_target"),
        Index(
            "uq_exam_target_whole_year",
            "exam_id",
            "year",
            unique=True,
            postgresql_where=group_id.is_(None),
        ),
    )

@final 
class QuestionType(enum.Enum):
    CHOISE = "choise"
    CHOICE = "choise"
    INPUT = "input"


@final 
class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    # Это сам вопрос 
    text: Mapped[str] = mapped_column(String(1000))
    # Тип вопроса 
    type: Mapped[QuestionType] = mapped_column()
    points: Mapped[int] = mapped_column(default=1)
    position: Mapped[int] = mapped_column(default=0)

    exam: Mapped["Exam"] = relationship(back_populates="questions")
    choices: Mapped[list["Choice"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", passive_deletes=True
    )
    inputs: Mapped[list["Input"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", passive_deletes=True
    )
    session_answers: Mapped[list["ExamSessionAnswer"]] = relationship(
        back_populates="question", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint("points >= 1", name="ck_question_points_positive"),
        CheckConstraint("position >= 0", name="ck_question_position_nonnegative"),
        UniqueConstraint("exam_id", "position", name="uq_question_exam_position"),
    )
    

@final 
class Choice(Base):
    __tablename__ = "choices"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    text: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(default=False)

    question: Mapped["Question"] = relationship(back_populates="choices")
    session_answers: Mapped[list["ExamSessionAnswer"]] = relationship(
        back_populates="choice", passive_deletes=True
    )
    
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
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    text: Mapped[str] = mapped_column(String(255))

    question: Mapped["Question"] = relationship(back_populates="inputs")

    __table_args__ = (
        UniqueConstraint("question_id", name="uq_input_question"),
    )







# ============== Студент часть

class ExamSessionStatus(enum.Enum):
    STARTED = "started"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


@final 
class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    status: Mapped[ExamSessionStatus] = mapped_column() 
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    answers: Mapped[dict | list] = mapped_column(JSONB, nullable=True, default=dict)
    score: Mapped[int | None] = mapped_column(nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    exam: Mapped["Exam"] = relationship(back_populates="sessions")
    user: Mapped["User"] = relationship()
    structured_answers: Mapped[list["ExamSessionAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "exam_id", name="uq_exam_session_user_exam"),
    )


@final
class ExamSessionAnswer(Base):
    __tablename__ = "exam_session_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("exam_sessions.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    choice_id: Mapped[int | None] = mapped_column(
        ForeignKey("choices.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    awarded_points: Mapped[int | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["ExamSession"] = relationship(back_populates="structured_answers")
    question: Mapped["Question"] = relationship(back_populates="session_answers")
    choice: Mapped["Choice | None"] = relationship(back_populates="session_answers")

    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_session_question_answer"),
        CheckConstraint(
            "(choice_id IS NULL) OR (text IS NULL)",
            name="ck_session_answer_single_value",
        ),
        CheckConstraint(
            "awarded_points IS NULL OR awarded_points >= 0",
            name="ck_session_answer_awarded_nonnegative",
        ),
    )







