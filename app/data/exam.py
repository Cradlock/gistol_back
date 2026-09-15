from datetime import datetime

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import DuplicateError, NotFoundError
from app.data.common import handle_integrity_error
from app.models.exam import (
    Choice,
    Exam,
    ExamSession,
    ExamSessionAnswer,
    ExamSessionStatus,
    ExamTargets,
    Input,
    Question,
    QuestionType,
)
from app.models.groups import Group
from app.models.user import User


def _exam_options():
    return (
        selectinload(Exam.targets),
        selectinload(Exam.questions).selectinload(Question.choices),
        selectinload(Exam.questions).selectinload(Question.inputs),
    )


def auto_choice_points(question: Question, choice_id: int | None) -> int:
    correct = next((choice for choice in question.choices if choice.is_correct), None)
    return question.points if correct is not None and choice_id == correct.id else 0


def reviewed_input_points(question: Question, accepted: bool) -> int:
    return question.points if accepted else 0


def score_delta(previous_score: int | None, new_score: int) -> int:
    return new_score - (previous_score or 0)


class ExamDataSQLAlchemy:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_exam(self, exam_id: int) -> Exam | None:
        result = await self.db.execute(
            select(Exam).options(*_exam_options()).where(Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    async def list_exams(
        self,
        page: int,
        page_size: int,
        search: str | None,
        group_id: int | None = None,
    ):
        base = select(Exam)
        if search:
            pattern = f"%{search.strip()}%"
            base = base.where(or_(Exam.title.ilike(pattern), Exam.theme.ilike(pattern)))
        if group_id is not None:
            group = await self.get_group(group_id)
            if group is None:
                return [], 0
            target_match = (
                select(ExamTargets.id)
                .where(
                    ExamTargets.exam_id == Exam.id,
                    or_(
                        ExamTargets.group_id == group_id,
                        and_(
                            ExamTargets.group_id.is_(None),
                            ExamTargets.year == group.year,
                        ),
                    ),
                )
                .exists()
            )
            base = base.where(target_match)
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = await self.db.execute(
            base.order_by(Exam.start_at.desc(), Exam.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows.scalars()), total

    @handle_integrity_error
    async def create_exam(self, values: dict) -> Exam:
        exam = Exam(**values)
        self.db.add(exam)
        await self.db.commit()
        return (await self.get_exam(exam.id))  # type: ignore[return-value]

    @handle_integrity_error
    async def update_exam(self, exam_id: int, values: dict) -> Exam:
        result = await self.db.execute(
            update(Exam).where(Exam.id == exam_id).values(**values).returning(Exam.id)
        )
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Exam not found")
        await self.db.commit()
        return (await self.get_exam(exam_id))  # type: ignore[return-value]

    async def delete_exam(self, exam_id: int) -> None:
        result = await self.db.execute(delete(Exam).where(Exam.id == exam_id))
        if result.rowcount == 0:
            raise NotFoundError("Exam not found")
        await self.db.commit()

    async def has_sessions(self, exam_id: int) -> bool:
        return bool(
            (await self.db.execute(select(ExamSession.id).where(ExamSession.exam_id == exam_id).limit(1)))
            .scalar_one_or_none()
        )

    async def get_group(self, group_id: int) -> Group | None:
        return await self.db.get(Group, group_id)

    @handle_integrity_error
    async def create_target(self, exam_id: int, values: dict) -> ExamTargets:
        target = ExamTargets(exam_id=exam_id, **values)
        self.db.add(target)
        await self.db.commit()
        await self.db.refresh(target)
        return target

    async def get_target(self, exam_id: int, target_id: int) -> ExamTargets | None:
        return (
            await self.db.execute(
                select(ExamTargets).where(
                    ExamTargets.id == target_id, ExamTargets.exam_id == exam_id
                )
            )
        ).scalar_one_or_none()

    @handle_integrity_error
    async def update_target(self, exam_id: int, target_id: int, values: dict) -> ExamTargets:
        target = await self.get_target(exam_id, target_id)
        if target is None:
            raise NotFoundError("Exam target not found")
        for key, value in values.items():
            setattr(target, key, value)
        await self.db.commit()
        await self.db.refresh(target)
        return target

    async def delete_target(self, exam_id: int, target_id: int) -> None:
        result = await self.db.execute(
            delete(ExamTargets).where(
                ExamTargets.id == target_id, ExamTargets.exam_id == exam_id
            )
        )
        if result.rowcount == 0:
            raise NotFoundError("Exam target not found")
        await self.db.commit()

    @handle_integrity_error
    async def create_question(self, exam_id: int, values: dict) -> Question:
        choices = values.pop("choices", [])
        expected = values.pop("expected_answer", None)
        question = Question(exam_id=exam_id, **values)
        question.choices = [Choice(**choice) for choice in choices]
        if expected is not None:
            question.inputs = [Input(text=expected)]
        self.db.add(question)
        await self.db.commit()
        return (await self.get_question(exam_id, question.id))  # type: ignore[return-value]

    async def get_question(self, exam_id: int, question_id: int) -> Question | None:
        result = await self.db.execute(
            select(Question)
            .options(selectinload(Question.choices), selectinload(Question.inputs))
            .where(Question.id == question_id, Question.exam_id == exam_id)
        )
        return result.scalar_one_or_none()

    @handle_integrity_error
    async def update_question(self, exam_id: int, question_id: int, values: dict) -> Question:
        question = await self.get_question(exam_id, question_id)
        if question is None:
            raise NotFoundError("Question not found")
        choices = values.pop("choices", [])
        expected = values.pop("expected_answer", None)
        for key, value in values.items():
            setattr(question, key, value)
        question.choices.clear()
        question.inputs.clear()
        question.choices.extend(Choice(**choice) for choice in choices)
        if expected is not None:
            question.inputs.append(Input(text=expected))
        await self.db.commit()
        return (await self.get_question(exam_id, question_id))  # type: ignore[return-value]

    async def delete_question(self, exam_id: int, question_id: int) -> None:
        result = await self.db.execute(
            delete(Question).where(Question.id == question_id, Question.exam_id == exam_id)
        )
        if result.rowcount == 0:
            raise NotFoundError("Question not found")
        await self.db.commit()

    async def list_available(
        self, user: User, now: datetime, page: int, page_size: int
    ):
        target_exists = (
            select(ExamTargets.id)
            .where(
                ExamTargets.exam_id == Exam.id,
                ExamTargets.year == user.year,
                or_(ExamTargets.group_id.is_(None), ExamTargets.group_id == user.group_id),
            )
            .exists()
        )
        base = select(Exam).where(
            target_exists,
            Exam.start_at <= now,
            Exam.start_at + Exam.duration_minutes * func.make_interval(0, 0, 0, 0, 0, 1) > now,
        )
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        result = await self.db.execute(
            base.order_by(Exam.start_at, Exam.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), total

    async def is_exam_available(self, exam_id: int, user: User) -> bool:
        target = (
            await self.db.execute(
                select(ExamTargets.id).where(
                    ExamTargets.exam_id == exam_id,
                    ExamTargets.year == user.year,
                    or_(ExamTargets.group_id.is_(None), ExamTargets.group_id == user.group_id),
                ).limit(1)
            )
        ).scalar_one_or_none()
        return target is not None

    async def get_session(self, session_id: int) -> ExamSession | None:
        result = await self.db.execute(
            select(ExamSession)
            .options(
                selectinload(ExamSession.exam).selectinload(Exam.questions).selectinload(Question.choices),
                selectinload(ExamSession.exam).selectinload(Exam.questions).selectinload(Question.inputs),
                selectinload(ExamSession.structured_answers)
                .selectinload(ExamSessionAnswer.question)
                .selectinload(Question.choices),
                selectinload(ExamSession.structured_answers).selectinload(ExamSessionAnswer.choice),
                selectinload(ExamSession.user),
            )
            .where(ExamSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_for_user_exam(self, user_id: int, exam_id: int):
        return (
            await self.db.execute(
                select(ExamSession).where(
                    ExamSession.user_id == user_id, ExamSession.exam_id == exam_id
                )
            )
        ).scalar_one_or_none()

    @handle_integrity_error
    async def create_session(self, user_id: int, exam_id: int, now: datetime):
        session = ExamSession(
            user_id=user_id,
            exam_id=exam_id,
            status=ExamSessionStatus.STARTED,
            started_at=now,
            answers={},
        )
        self.db.add(session)
        await self.db.commit()
        return (await self.get_session(session.id))  # type: ignore[return-value]

    @handle_integrity_error
    async def upsert_answer(
        self, session_id: int, question_id: int, choice_id: int | None, text: str | None
    ):
        answer = (
            await self.db.execute(
                select(ExamSessionAnswer).where(
                    ExamSessionAnswer.session_id == session_id,
                    ExamSessionAnswer.question_id == question_id,
                )
            )
        ).scalar_one_or_none()
        if answer is None:
            answer = ExamSessionAnswer(session_id=session_id, question_id=question_id)
            self.db.add(answer)
        answer.choice_id = choice_id
        answer.text = text
        answer.awarded_points = None
        answer.reviewed_at = None
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def list_sessions(self, exam_id: int):
        if await self.get_exam(exam_id) is None:
            raise NotFoundError("Exam not found")
        result = await self.db.execute(
            select(ExamSession)
            .options(selectinload(ExamSession.user))
            .where(ExamSession.exam_id == exam_id)
            .order_by(ExamSession.id)
        )
        sessions = list(result.scalars())
        return sessions, len(sessions)

    async def submit_session(self, session_id: int, now: datetime) -> ExamSession:
        session = await self.get_session(session_id)
        if session is None:
            raise NotFoundError("Exam session not found")
        existing = {a.question_id: a for a in session.structured_answers}
        pending = False
        subtotal = 0
        for question in session.exam.questions:
            answer = existing.get(question.id)
            if answer is None:
                answer = ExamSessionAnswer(session_id=session.id, question_id=question.id)
                self.db.add(answer)
            if question.type == QuestionType.CHOISE:
                answer.awarded_points = auto_choice_points(question, answer.choice_id)
                answer.reviewed_at = now
                subtotal += answer.awarded_points
            elif answer.text is None:
                answer.awarded_points = 0
                answer.reviewed_at = now
            else:
                answer.awarded_points = None
                answer.reviewed_at = None
                pending = True
        session.status = ExamSessionStatus.SUBMITTED
        session.submitted_at = now
        if pending:
            session.score = None
            session.reviewed_at = None
        else:
            old_score = session.score
            session.score = subtotal
            session.reviewed_at = now
            await self.db.execute(
                update(User)
                .where(User.id == session.user_id)
                .values(scores=func.greatest(0, User.scores + score_delta(old_score, subtotal)))
            )
        await self.db.commit()
        return (await self.get_session(session_id))  # type: ignore[return-value]

    async def review_answer(
        self, session_id: int, answer_id: int, accepted: bool, now: datetime
    ) -> ExamSession:
        session = await self.get_session(session_id)
        if session is None:
            raise NotFoundError("Exam session not found")
        answer = next((a for a in session.structured_answers if a.id == answer_id), None)
        if answer is None:
            raise NotFoundError("Session answer not found")
        if answer.question.type != QuestionType.INPUT or answer.text is None:
            raise ValueError("Only submitted text answers can be reviewed")
        answer.awarded_points = reviewed_input_points(answer.question, accepted)
        answer.reviewed_at = now

        if all(a.awarded_points is not None for a in session.structured_answers):
            old_score = session.score
            new_score = sum(a.awarded_points or 0 for a in session.structured_answers)
            session.score = new_score
            session.reviewed_at = now
            await self.db.execute(
                update(User)
                .where(User.id == session.user_id)
                .values(scores=func.greatest(0, User.scores + score_delta(old_score, new_score)))
            )
        await self.db.commit()
        return (await self.get_session(session_id))  # type: ignore[return-value]
