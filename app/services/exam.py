from datetime import datetime, timedelta, timezone

from app.core.errors import DuplicateError, NotFoundError
from app.core.exceptions import (
    bad_request_exception,
    conflict_exception,
    forbidden_exception,
    not_found_exception,
)
from app.data.exam import ExamDataSQLAlchemy
from app.models.exam import ExamSessionStatus, QuestionType
from app.models.user import User
from app.schemas.exam import (
    AnswerSavedResponse,
    ExamListResponse,
    ExamResponse,
    ExamSummary,
    QuestionResponse,
    SessionListResponse,
    SessionStartResponse,
    SessionSubmitResponse,
    SessionSummary,
    SessionTakeResponse,
    StudentChoiceResponse,
    StudentQuestionResponse,
    TargetResponse,
    TeacherAnswerResponse,
    TeacherSessionDetail,
)


class ExamService:
    def __init__(self, repo: ExamDataSQLAlchemy):
        self.repo = repo

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _deadline(exam) -> datetime:
        return exam.start_at + timedelta(minutes=exam.duration_minutes)

    @staticmethod
    def _question(question, teacher: bool = True):
        choices = [
            (
                {"id": c.id, "text": c.text, "is_correct": c.is_correct}
                if teacher
                else StudentChoiceResponse(id=c.id, text=c.text)
            )
            for c in question.choices
        ]
        if teacher:
            return QuestionResponse(
                id=question.id,
                text=question.text,
                type=question.type,
                points=question.points,
                position=question.position,
                choices=choices,
                expected_answer=question.inputs[0].text if question.inputs else None,
            )
        return StudentQuestionResponse(
            id=question.id,
            text=question.text,
            type=question.type,
            points=question.points,
            position=question.position,
            choices=choices,
        )

    @classmethod
    def _exam(cls, exam):
        return ExamResponse(
            id=exam.id,
            title=exam.title,
            theme=exam.theme,
            start_at=exam.start_at,
            duration_minutes=exam.duration_minutes,
            targets=[TargetResponse.model_validate(t) for t in exam.targets],
            questions=[cls._question(q) for q in exam.questions],
        )

    @classmethod
    def _summary(cls, exam):
        return ExamSummary(
            id=exam.id,
            title=exam.title,
            theme=exam.theme,
            start_at=exam.start_at,
            duration_minutes=exam.duration_minutes,
            deadline=cls._deadline(exam),
        )

    async def list_exams(
        self,
        page: int,
        page_size: int,
        search: str | None,
        group_id: int | None = None,
    ):
        exams, total = await self.repo.list_exams(page, page_size, search, group_id)
        return ExamListResponse(total=total, exams=[self._summary(e) for e in exams])

    async def create_exam(self, values: dict):
        return self._exam(await self.repo.create_exam(values))

    async def get_exam(self, exam_id: int):
        exam = await self.repo.get_exam(exam_id)
        if exam is None:
            raise not_found_exception("Exam not found")
        return self._exam(exam)

    async def update_exam(self, exam_id: int, values: dict):
        if await self.repo.get_exam(exam_id) is None:
            raise not_found_exception("Exam not found")
        if not values:
            return await self.get_exam(exam_id)
        try:
            return self._exam(await self.repo.update_exam(exam_id, values))
        except NotFoundError:
            raise not_found_exception("Exam not found")

    async def delete_exam(self, exam_id: int):
        try:
            await self.repo.delete_exam(exam_id)
        except NotFoundError:
            raise not_found_exception("Exam not found")

    async def _ensure_mutable(self, exam_id: int):
        if await self.repo.get_exam(exam_id) is None:
            raise not_found_exception("Exam not found")
        if await self.repo.has_sessions(exam_id):
            raise conflict_exception("Exam targets and questions are locked after a session starts")

    async def _validate_target(self, values: dict):
        group_id = values.get("group_id")
        if group_id is not None:
            group = await self.repo.get_group(group_id)
            if group is None:
                raise not_found_exception("Group not found")
            if group.year != values["year"]:
                raise bad_request_exception("Target year must match the group year")

    async def create_target(self, exam_id: int, values: dict):
        await self._ensure_mutable(exam_id)
        await self._validate_target(values)
        try:
            return TargetResponse.model_validate(await self.repo.create_target(exam_id, values))
        except DuplicateError:
            raise conflict_exception("Exam target already exists")

    async def list_targets(self, exam_id: int):
        exam = await self.repo.get_exam(exam_id)
        if exam is None:
            raise not_found_exception("Exam not found")
        return [TargetResponse.model_validate(target) for target in exam.targets]

    async def get_target(self, exam_id: int, target_id: int):
        target = await self.repo.get_target(exam_id, target_id)
        if target is None:
            raise not_found_exception("Exam target not found")
        return TargetResponse.model_validate(target)

    async def update_target(self, exam_id: int, target_id: int, values: dict):
        await self._ensure_mutable(exam_id)
        await self._validate_target(values)
        try:
            return TargetResponse.model_validate(
                await self.repo.update_target(exam_id, target_id, values)
            )
        except NotFoundError:
            raise not_found_exception("Exam target not found")
        except DuplicateError:
            raise conflict_exception("Exam target already exists")

    async def delete_target(self, exam_id: int, target_id: int):
        await self._ensure_mutable(exam_id)
        try:
            await self.repo.delete_target(exam_id, target_id)
        except NotFoundError:
            raise not_found_exception("Exam target not found")

    async def create_question(self, exam_id: int, values: dict):
        await self._ensure_mutable(exam_id)
        try:
            return self._question(await self.repo.create_question(exam_id, values))
        except DuplicateError:
            raise conflict_exception("Question position already exists")

    async def list_questions(self, exam_id: int):
        exam = await self.repo.get_exam(exam_id)
        if exam is None:
            raise not_found_exception("Exam not found")
        return [self._question(question) for question in exam.questions]

    async def get_question(self, exam_id: int, question_id: int):
        question = await self.repo.get_question(exam_id, question_id)
        if question is None:
            raise not_found_exception("Question not found")
        return self._question(question)

    async def update_question(self, exam_id: int, question_id: int, values: dict):
        await self._ensure_mutable(exam_id)
        try:
            return self._question(
                await self.repo.update_question(exam_id, question_id, values)
            )
        except NotFoundError:
            raise not_found_exception("Question not found")
        except DuplicateError:
            raise conflict_exception("Question position already exists")

    async def delete_question(self, exam_id: int, question_id: int):
        await self._ensure_mutable(exam_id)
        try:
            await self.repo.delete_question(exam_id, question_id)
        except NotFoundError:
            raise not_found_exception("Question not found")

    async def list_available(self, user: User, page: int, page_size: int):
        if user.group_id is None or user.year is None:
            raise bad_request_exception("Student group and year must be assigned")
        exams, total = await self.repo.list_available(user, self._now(), page, page_size)
        return ExamListResponse(total=total, exams=[self._summary(e) for e in exams])

    async def start_session(self, exam_id: int, user: User):
        exam = await self.repo.get_exam(exam_id)
        if exam is None:
            raise not_found_exception("Exam not found")
        now = self._now()
        if not await self.repo.is_exam_available(exam_id, user):
            raise forbidden_exception("Exam is not targeted to this student")
        if now < exam.start_at or now >= self._deadline(exam):
            raise bad_request_exception("Exam is not available at this time")
        if await self.repo.get_session_for_user_exam(user.id, exam_id) is not None:
            raise conflict_exception("Exam session already exists")
        try:
            session = await self.repo.create_session(user.id, exam_id, now)
        except DuplicateError:
            raise conflict_exception("Exam session already exists")
        return SessionStartResponse(
            id=session.id,
            exam_id=exam.id,
            status=session.status,
            started_at=session.started_at,
            deadline=self._deadline(exam),
        )

    async def _owned_active_session(self, session_id: int, user: User):
        session = await self.repo.get_session(session_id)
        if session is None:
            raise not_found_exception("Exam session not found")
        if session.user_id != user.id:
            raise forbidden_exception("Exam session belongs to another student")
        if session.status != ExamSessionStatus.STARTED:
            raise conflict_exception("Exam session is no longer editable")
        if self._now() >= self._deadline(session.exam):
            raise bad_request_exception("Exam deadline has passed")
        return session

    async def take_session(self, session_id: int, user: User):
        session = await self._owned_active_session(session_id, user)
        exam = session.exam
        return SessionTakeResponse(
            id=session.id,
            exam_id=exam.id,
            status=session.status,
            started_at=session.started_at,
            deadline=self._deadline(exam),
            title=exam.title,
            theme=exam.theme,
            questions=[self._question(q, teacher=False) for q in exam.questions],
        )

    async def save_answer(
        self, session_id: int, question_id: int, user: User, values: dict
    ):
        session = await self._owned_active_session(session_id, user)
        question = next((q for q in session.exam.questions if q.id == question_id), None)
        if question is None:
            raise not_found_exception("Question not found in this exam")
        choice_id, text = values.get("choice_id"), values.get("text")
        if question.type == QuestionType.CHOISE:
            if text is not None or not any(c.id == choice_id for c in question.choices):
                raise bad_request_exception("A valid choice_id is required for this question")
        elif choice_id is not None or text is None:
            raise bad_request_exception("A text answer is required for this question")
        answer = await self.repo.upsert_answer(
            session_id, question_id, choice_id=choice_id, text=text
        )
        return AnswerSavedResponse.model_validate(answer)

    async def submit_session(self, session_id: int, user: User):
        await self._owned_active_session(session_id, user)
        session = await self.repo.submit_session(session_id, self._now())
        return SessionSubmitResponse(
            id=session.id,
            exam_id=session.exam_id,
            status=session.status,
            submitted_at=session.submitted_at,
            reviewed_at=session.reviewed_at,
            score=session.score,
        )

    async def list_sessions(self, exam_id: int):
        try:
            sessions, total = await self.repo.list_sessions(exam_id)
        except NotFoundError:
            raise not_found_exception("Exam not found")
        return SessionListResponse(
            total=total,
            sessions=[
                SessionSummary(
                    id=s.id,
                    user_id=s.user_id,
                    student_name=s.user.fio,
                    status=s.status,
                    started_at=s.started_at,
                    submitted_at=s.submitted_at,
                    reviewed_at=s.reviewed_at,
                    score=s.score,
                )
                for s in sessions
            ],
        )

    @classmethod
    def _teacher_session(cls, session):
        answers = []
        for answer in sorted(
            session.structured_answers, key=lambda a: (a.question.position, a.id)
        ):
            question = answer.question
            answers.append(
                TeacherAnswerResponse(
                    id=answer.id,
                    question_id=question.id,
                    question_text=question.text,
                    question_type=question.type,
                    question_points=question.points,
                    choice_id=answer.choice_id,
                    choice_text=answer.choice.text if answer.choice else None,
                    text=answer.text,
                    awarded_points=answer.awarded_points,
                    reviewed_at=answer.reviewed_at,
                    choices=[
                        {"id": c.id, "text": c.text, "is_correct": c.is_correct}
                        for c in question.choices
                    ],
                )
            )
        return TeacherSessionDetail(
            id=session.id,
            user_id=session.user_id,
            student_name=session.user.fio,
            exam_id=session.exam_id,
            exam_title=session.exam.title,
            exam_theme=session.exam.theme,
            status=session.status,
            started_at=session.started_at,
            submitted_at=session.submitted_at,
            reviewed_at=session.reviewed_at,
            score=session.score,
            answers=answers,
        )

    async def get_session_detail(self, session_id: int):
        session = await self.repo.get_session(session_id)
        if session is None:
            raise not_found_exception("Exam session not found")
        return self._teacher_session(session)

    async def review_answer(self, session_id: int, answer_id: int, accepted: bool):
        session = await self.repo.get_session(session_id)
        if session is None:
            raise not_found_exception("Exam session not found")
        if session.status != ExamSessionStatus.SUBMITTED:
            raise conflict_exception("Exam session has not been submitted")
        try:
            reviewed = await self.repo.review_answer(
                session_id, answer_id, accepted, self._now()
            )
        except NotFoundError as exc:
            raise not_found_exception(exc.message)
        except ValueError as exc:
            raise bad_request_exception(str(exc))
        return self._teacher_session(reviewed)
