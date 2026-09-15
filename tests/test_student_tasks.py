from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest

from fastapi import HTTPException

from app.dependencies import get_current_student_or_higher
from app.models.user import User, UserRoleEnum
from app.services.task import TaskService


class FakeTaskRepo:
    def __init__(self):
        self.available_call = None
        self.history_call = None
        self.task = None
        self.existing_answer = None

    async def list_available_for_student(self, **kwargs):
        self.available_call = kwargs
        return [], 0

    async def list_answer_history(self, user_id, page, page_size):
        self.history_call = (user_id, page, page_size)
        return [], 0

    async def get_by_id(self, task_id):
        return self.task

    async def get_answer_for_user_task(self, user_id, task_id):
        return self.existing_answer

    async def create_answer(self, user_id, task_id, text):
        return SimpleNamespace(user_id=user_id, task_id=task_id, text=text)


class StudentTaskTests(unittest.IsolatedAsyncioTestCase):
    async def test_dependency_allows_student_or_higher(self):
        for role in (
            UserRoleEnum.STUDENT,
            UserRoleEnum.TEACHER,
            UserRoleEnum.SUPERADMIN,
        ):
            user = User(id=1, role=role, group_id=4)
            self.assertIs(await get_current_student_or_higher(user), user)

    async def test_dependency_rejects_lower_role_with_403(self):
        user = User(id=1, role=UserRoleEnum.NOT_CONFIRMED)
        with self.assertRaises(HTTPException) as raised:
            await get_current_student_or_higher(user)
        self.assertEqual(raised.exception.status_code, 403)

    async def test_available_tasks_uses_group_from_user(self):
        repo = FakeTaskRepo()
        service = TaskService(repo)
        user = User(id=7, role=UserRoleEnum.STUDENT, group_id=13)

        response = await service.list_available_tasks(user, page=2, page_size=20)

        self.assertEqual(response.total, 0)
        self.assertEqual(repo.available_call["user_id"], 7)
        self.assertEqual(repo.available_call["group_id"], 13)
        self.assertEqual(repo.available_call["page"], 2)
        self.assertEqual(repo.available_call["page_size"], 20)

    async def test_history_is_scoped_to_current_user(self):
        repo = FakeTaskRepo()
        service = TaskService(repo)
        user = User(id=22, role=UserRoleEnum.STUDENT, group_id=3)

        await service.get_answer_history(user, page=3, page_size=20)

        self.assertEqual(repo.history_call, (22, 3, 20))

    async def test_answer_rejects_task_from_another_group(self):
        now = datetime.now(timezone.utc)
        repo = FakeTaskRepo()
        repo.task = SimpleNamespace(
            group_id=99,
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
        )
        service = TaskService(repo)
        user = User(id=7, role=UserRoleEnum.STUDENT, group_id=13)

        with self.assertRaises(HTTPException) as raised:
            await service.submit_answer(1, user, "answer")
        self.assertEqual(raised.exception.status_code, 403)

    async def test_answer_rejects_duplicate(self):
        now = datetime.now(timezone.utc)
        repo = FakeTaskRepo()
        repo.task = SimpleNamespace(
            group_id=13,
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
        )
        repo.existing_answer = SimpleNamespace(id=1)
        service = TaskService(repo)
        user = User(id=7, role=UserRoleEnum.STUDENT, group_id=13)

        with self.assertRaises(HTTPException) as raised:
            await service.submit_answer(1, user, "answer")
        self.assertEqual(raised.exception.status_code, 409)

    async def test_answer_rejects_expired_task(self):
        now = datetime.now(timezone.utc)
        repo = FakeTaskRepo()
        repo.task = SimpleNamespace(
            group_id=13,
            start_at=now - timedelta(hours=2),
            end_at=now - timedelta(hours=1),
        )
        service = TaskService(repo)
        user = User(id=7, role=UserRoleEnum.STUDENT, group_id=13)

        with self.assertRaises(HTTPException) as raised:
            await service.submit_answer(1, user, "answer")
        self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
