from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from fastapi import HTTPException
from pydantic import ValidationError

from app.dependencies import get_current_teacher
from app.data.exam import (
    ExamDataSQLAlchemy,
    auto_choice_points,
    reviewed_input_points,
    score_delta,
)
from app.models.exam import ExamSessionStatus, QuestionType
from app.models.user import User, UserRoleEnum
from app.models.years import Year
from app.schemas.exam import AnswerUpsert, QuestionWrite
from app.services.exam import ExamService


class FakeExamRepo:
    def __init__(self):
        self.exam = None
        self.session = None
        self.duplicate = None
        self.targeted = True
        self.has_any_sessions = False

    async def get_exam(self, _exam_id):
        return self.exam

    async def has_sessions(self, _exam_id):
        return self.has_any_sessions

    async def is_exam_available(self, _exam_id, _user):
        return self.targeted

    async def get_session_for_user_exam(self, _user_id, _exam_id):
        return self.duplicate

    async def create_session(self, user_id, exam_id, now):
        return SimpleNamespace(
            id=9,
            user_id=user_id,
            exam_id=exam_id,
            status=ExamSessionStatus.STARTED,
            started_at=now,
        )

    async def get_session(self, _session_id):
        return self.session


def exam_at(start_at):
    return SimpleNamespace(
        id=3,
        title="Exam",
        theme="Theme",
        start_at=start_at,
        duration_minutes=60,
        targets=[],
        questions=[],
    )


class ExamServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = FakeExamRepo()
        self.service = ExamService(self.repo)
        self.user = User(
            id=7,
            role=UserRoleEnum.STUDENT,
            group_id=2,
            year=Year.FIRST,
            code="student",
        )

    async def test_start_rejects_exam_for_another_target(self):
        self.repo.exam = exam_at(datetime.now(timezone.utc) - timedelta(minutes=5))
        self.repo.targeted = False
        with self.assertRaises(HTTPException) as raised:
            await self.service.start_session(3, self.user)
        self.assertEqual(raised.exception.status_code, 403)

    async def test_start_rejects_exam_outside_fixed_window(self):
        self.repo.exam = exam_at(datetime.now(timezone.utc) - timedelta(hours=2))
        with self.assertRaises(HTTPException) as raised:
            await self.service.start_session(3, self.user)
        self.assertEqual(raised.exception.status_code, 400)

    async def test_start_rejects_duplicate_session(self):
        self.repo.exam = exam_at(datetime.now(timezone.utc) - timedelta(minutes=5))
        self.repo.duplicate = SimpleNamespace(id=1)
        with self.assertRaises(HTTPException) as raised:
            await self.service.start_session(3, self.user)
        self.assertEqual(raised.exception.status_code, 409)

    async def test_take_checks_student_ownership(self):
        exam = exam_at(datetime.now(timezone.utc) - timedelta(minutes=5))
        self.repo.session = SimpleNamespace(
            id=4,
            user_id=999,
            status=ExamSessionStatus.STARTED,
            exam=exam,
        )
        with self.assertRaises(HTTPException) as raised:
            await self.service.take_session(4, self.user)
        self.assertEqual(raised.exception.status_code, 403)

    async def test_question_mutation_locked_after_session_exists(self):
        self.repo.exam = exam_at(datetime.now(timezone.utc))
        self.repo.has_any_sessions = True
        with self.assertRaises(HTTPException) as raised:
            await self.service.create_question(
                3,
                {
                    "text": "Q",
                    "type": QuestionType.INPUT,
                    "points": 1,
                    "position": 0,
                    "choices": [],
                    "expected_answer": "A",
                },
            )
        self.assertEqual(raised.exception.status_code, 409)

    async def test_teacher_dependency_rejects_student(self):
        with self.assertRaises(HTTPException) as raised:
            await get_current_teacher(self.user)
        self.assertEqual(raised.exception.status_code, 403)

    async def test_teacher_dependency_allows_teacher(self):
        teacher = User(
            id=8,
            role=UserRoleEnum.TEACHER,
            group_id=None,
            year=None,
            code="teacher",
        )
        self.assertIs(await get_current_teacher(teacher), teacher)


class ExamValidationAndGradingTests(unittest.TestCase):
    def test_student_question_does_not_expose_answer_key(self):
        question = SimpleNamespace(
            id=1,
            text="Question",
            type=QuestionType.CHOISE,
            points=2,
            position=0,
            choices=[SimpleNamespace(id=4, text="Answer", is_correct=True)],
            inputs=[],
        )
        payload = ExamService._question(question, teacher=False).model_dump()
        self.assertNotIn("expected_answer", payload)
        self.assertNotIn("is_correct", payload["choices"][0])

    def test_choice_requires_two_options_and_one_correct(self):
        with self.assertRaises(ValidationError):
            QuestionWrite(
                text="Question",
                type=QuestionType.CHOISE,
                choices=[{"text": "Only", "is_correct": True}],
            )

    def test_input_requires_exactly_one_expected_answer(self):
        with self.assertRaises(ValidationError):
            QuestionWrite(text="Question", type=QuestionType.INPUT)

    def test_answer_requires_exactly_one_value(self):
        with self.assertRaises(ValidationError):
            AnswerUpsert(choice_id=1, text="both")

    def test_choice_autograding_is_binary(self):
        question = SimpleNamespace(
            points=4,
            choices=[
                SimpleNamespace(id=10, is_correct=False),
                SimpleNamespace(id=11, is_correct=True),
            ],
        )
        self.assertEqual(auto_choice_points(question, 11), 4)
        self.assertEqual(auto_choice_points(question, 10), 0)

    def test_manual_input_grading_is_binary(self):
        question = SimpleNamespace(points=7)
        self.assertEqual(reviewed_input_points(question, True), 7)
        self.assertEqual(reviewed_input_points(question, False), 0)

    def test_regrading_delta_is_idempotent(self):
        self.assertEqual(score_delta(None, 5), 5)
        self.assertEqual(score_delta(5, 5), 0)
        self.assertEqual(score_delta(5, 0), -5)


class ExamDataGradingTests(unittest.IsolatedAsyncioTestCase):
    async def test_submit_and_review_finalize_score_then_apply_regrade(self):
        db = AsyncMock()
        repo = ExamDataSQLAlchemy(db)
        choice_question = SimpleNamespace(
            id=1,
            type=QuestionType.CHOISE,
            points=3,
            choices=[SimpleNamespace(id=10, is_correct=True)],
        )
        input_question = SimpleNamespace(
            id=2,
            type=QuestionType.INPUT,
            points=5,
            choices=[],
        )
        choice_answer = SimpleNamespace(
            id=11,
            question_id=1,
            choice_id=10,
            text=None,
            question=choice_question,
            awarded_points=None,
            reviewed_at=None,
        )
        input_answer = SimpleNamespace(
            id=12,
            question_id=2,
            choice_id=None,
            text="Student answer",
            question=input_question,
            awarded_points=None,
            reviewed_at=None,
        )
        session = SimpleNamespace(
            id=7,
            user_id=8,
            exam_id=9,
            exam=SimpleNamespace(questions=[choice_question, input_question]),
            structured_answers=[choice_answer, input_answer],
            status=ExamSessionStatus.STARTED,
            submitted_at=None,
            reviewed_at=None,
            score=None,
        )
        repo.get_session = AsyncMock(return_value=session)
        now = datetime.now(timezone.utc)

        await repo.submit_session(session.id, now)
        self.assertEqual(choice_answer.awarded_points, 3)
        self.assertIsNone(input_answer.awarded_points)
        self.assertIsNone(session.score)

        await repo.review_answer(session.id, input_answer.id, True, now)
        self.assertEqual(session.score, 8)
        self.assertEqual(input_answer.awarded_points, 5)

        await repo.review_answer(session.id, input_answer.id, False, now)
        self.assertEqual(session.score, 3)
        self.assertEqual(input_answer.awarded_points, 0)
        self.assertEqual(db.execute.await_count, 2)


if __name__ == "__main__":
    unittest.main()
