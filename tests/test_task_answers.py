from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from pydantic import ValidationError

from app.models.task import StudentAnswerStatus
from app.models.years import Year
from app.schemas.task import TaskCreate
from app.services.task import to_answer_response, to_task_response


class TaskAnswerResponseTests(unittest.TestCase):
    def test_uses_fio_and_group_title(self):
        answer = SimpleNamespace(
            id=1,
            user_id=12,
            task_id=3,
            text="Ответ",
            status=StudentAnswerStatus.PENDING,
            submitted_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
            user=SimpleNamespace(
                fio="Иван Иванов",
                name="Иван",
                surname="Иванов",
                telegram_username=None,
                group=SimpleNamespace(title="БПИ-231"),
            ),
        )

        payload = to_answer_response(answer).model_dump()

        self.assertEqual(payload["student_name"], "Иван Иванов")
        self.assertEqual(payload["group_title"], "БПИ-231")
        self.assertEqual(payload["user_id"], 12)

    def test_falls_back_to_id_without_user(self):
        answer = SimpleNamespace(
            id=1,
            user_id=12,
            task_id=3,
            text="Ответ",
            status=StudentAnswerStatus.PENDING,
            submitted_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        )

        payload = to_answer_response(answer).model_dump()

        self.assertEqual(payload["student_name"], "#12")
        self.assertIsNone(payload["group_title"])


class TaskGroupsResponseTests(unittest.TestCase):
    def test_task_response_lists_all_groups(self):
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        task = SimpleNamespace(
            id=4,
            title="Задача",
            content="Текст",
            start_at=now,
            end_at=now,
            points=3,
            groups=[
                SimpleNamespace(
                    id=1,
                    title="БПИ-231",
                    year=Year.FIRST,
                    is_active=True,
                    created_date=now,
                ),
                SimpleNamespace(
                    id=2,
                    title="БПИ-232",
                    year=Year.FIRST,
                    is_active=True,
                    created_date=now,
                ),
            ],
        )

        payload = to_task_response(task).model_dump()

        self.assertEqual(payload["group_ids"], [1, 2])
        self.assertEqual(
            [group["title"] for group in payload["groups"]],
            ["БПИ-231", "БПИ-232"],
        )

    def test_create_requires_at_least_one_group(self):
        now = datetime(2026, 9, 27, tzinfo=timezone.utc)
        with self.assertRaises(ValidationError):
            TaskCreate(
                title="Задача",
                content="Текст",
                group_ids=[],
                start_at=now,
                end_at=now,
                points=1,
            )
