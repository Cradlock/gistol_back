from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from app.models.task import StudentAnswerStatus
from app.services.task import to_answer_response


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
