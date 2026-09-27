from types import SimpleNamespace
import unittest

from fastapi import HTTPException

from app.core.security import hash_password
from app.models.user import UserRoleEnum
from app.schemas.auth import AdminCodeUpdateRequest, AdminPasswordUpdateRequest
from app.services.auth import AuthService


class FakeAdminRepo:
    def __init__(self, user, other=None):
        self.user = user
        self.other = other
        self.updated = None

    async def get_by_field(self, field, value):
        if self.other is not None and getattr(self.other, field, None) == value:
            return self.other
        if getattr(self.user, field, None) == value:
            return self.user
        return None

    async def get_by_id(self, user_id):
        if self.user.id == user_id:
            return self.user
        return None

    async def update_user(self, user_id, update_data):
        self.updated = update_data
        for key, value in update_data.items():
            setattr(self.user, key, value)
        return self.user


def _teacher(password="secret"):
    return SimpleNamespace(
        id=4,
        code="admin",
        password_hash=hash_password(password),
        role=UserRoleEnum.TEACHER,
        name="Ada",
        surname="Admin",
        deleted=False,
    )


class AdminCredentialTests(unittest.IsolatedAsyncioTestCase):
    async def test_updates_admin_login(self):
        user = _teacher()
        service = AuthService(FakeAdminRepo(user))

        result = await service.update_admin_code(
            user,
            AdminCodeUpdateRequest(current_password="secret", code="new-admin"),
        )

        self.assertEqual(result.code, "new-admin")

    async def test_rejects_wrong_password(self):
        user = _teacher()
        service = AuthService(FakeAdminRepo(user))

        with self.assertRaises(HTTPException) as raised:
            await service.update_admin_password(
                user,
                AdminPasswordUpdateRequest(
                    current_password="wrong",
                    new_password="new-secret",
                ),
            )
        self.assertEqual(raised.exception.status_code, 401)

    async def test_rejects_taken_login(self):
        user = _teacher()
        other = SimpleNamespace(id=9, code="taken")
        service = AuthService(FakeAdminRepo(user, other=other))

        with self.assertRaises(HTTPException) as raised:
            await service.update_admin_code(
                user,
                AdminCodeUpdateRequest(current_password="secret", code="taken"),
            )
        self.assertEqual(raised.exception.status_code, 409)

    async def test_updates_password_hash(self):
        user = _teacher()
        repo = FakeAdminRepo(user)
        service = AuthService(repo)

        await service.update_admin_password(
            user,
            AdminPasswordUpdateRequest(
                current_password="secret",
                new_password="new-secret",
            ),
        )

        self.assertIn("password_hash", repo.updated)
        self.assertNotEqual(repo.updated["password_hash"], "new-secret")


if __name__ == "__main__":
    unittest.main()
