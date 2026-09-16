from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from fastapi import HTTPException

from app.core.errors import DuplicateError
from app.models.user import UserRoleEnum
from app.models.years import Year
from app.schemas.auth import UserResponse
from app.schemas.students import StudentComplete
from app.services.auth import AuthService
from app.services.student import StudentService


class FakeAuthRepo:
    def __init__(self):
        self.user = None
        self.created = None
        self.raise_duplicate = False

    async def get_by_field(self, field, value):
        return self.user

    async def create_user(self, data):
        if self.raise_duplicate:
            self.raise_duplicate = False
            raise DuplicateError()
        self.created = data
        self.user = SimpleNamespace(
            id=11,
            telegram_id=data["telegram_id"],
            deleted=False,
            name=None,
            surname=None,
            scores=0,
            year=1,
            group_id=None,
            group=None,
            role=UserRoleEnum.NOT_CONFIRMED,
        )
        return self.user


class FakeStudentRepo:
    def __init__(self):
        self.saved = None
        self.user = SimpleNamespace(
            id=7,
            name="Ann",
            surname="Lee",
            scores=0,
            year=Year.SECOND,
            group_id=4,
            group=SimpleNamespace(
                id=4,
                title="BPI-231",
                year=Year.SECOND,
                is_active=True,
                created_date=datetime.now(timezone.utc),
            ),
            role=UserRoleEnum.NOT_CONFIRMED,
        )

    async def complete_student(self, user_id, data):
        self.saved = (user_id, data)
        return {
            "id": user_id,
            "name": data.name,
            "surname": data.surname,
            "scores": 0,
            "year": int(data.year),
            "group_id": data.group_id,
            "group": {
                "id": 4,
                "title": "BPI-231",
                "year": 2,
                "is_active": True,
                "created_date": datetime(2026, 1, 1, tzinfo=timezone.utc),
            },
            "role": int(UserRoleEnum.NOT_CONFIRMED),
        }


class TelegramAuthTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = FakeAuthRepo()
        self.service = AuthService(self.repo)
        self.service.verify_telegram_token = AsyncMock(
            return_value={"id": 555, "username": "ann"}
        )

    async def test_creates_user_when_telegram_id_is_missing(self):
        result = await self.service.get_telegram_user("token")

        self.assertEqual(self.repo.created["telegram_id"], "555")
        self.assertEqual(self.repo.created["telegram_username"], "ann")
        self.assertEqual(result["user"].id, 11)
        self.assertIn("access_token", result)
        self.assertIn("refresh_token", result)
        serialized = UserResponse.model_validate(result["user"])
        self.assertIsNone(serialized.name)
        self.assertIsNone(serialized.group_id)
        self.assertFalse(serialized.confirmed)

    async def test_returns_existing_user(self):
        self.repo.user = SimpleNamespace(id=3, deleted=False)

        result = await self.service.get_telegram_user("token")

        self.assertIsNone(self.repo.created)
        self.assertEqual(result["user"].id, 3)

    async def test_create_race_reloads_existing_user(self):
        self.repo.raise_duplicate = True
        self.repo.user = SimpleNamespace(id=9, deleted=False)

        result = await self.service.get_telegram_user("token")

        self.assertEqual(result["user"].id, 9)

    async def test_rejects_deleted_account(self):
        self.repo.user = SimpleNamespace(id=3, deleted=True)

        with self.assertRaises(HTTPException) as raised:
            await self.service.get_telegram_user("token")
        self.assertEqual(raised.exception.status_code, 403)

    async def test_rejects_token_without_telegram_id(self):
        self.service.verify_telegram_token = AsyncMock(return_value={})

        with self.assertRaises(HTTPException) as raised:
            await self.service.get_telegram_user("token")
        self.assertEqual(raised.exception.status_code, 401)


class CompleteStudentTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_profile_returns_group_and_year(self):
        repo = FakeStudentRepo()
        service = StudentService(repo)
        user = SimpleNamespace(id=7)
        data = StudentComplete(
            name="Ann",
            surname="Lee",
            group_id=4,
            year=Year.SECOND,
        )

        response = await service.complete_student(user, data)

        self.assertEqual(repo.saved[0], 7)
        self.assertEqual(response.group_id, 4)
        self.assertEqual(response.year, 2)
        self.assertEqual(response.group.title, "BPI-231")


class TelegramJwksFetchTests(unittest.TestCase):
    def test_fetch_data_decodes_gzip_jwks(self):
        import gzip
        import json
        from unittest.mock import patch

        import httpx

        from app.utils.jwks import TelegramJWKClient

        payload = {"keys": []}
        compressed = gzip.compress(json.dumps(payload).encode("utf-8"))
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={
                    "Content-Type": "application/json",
                    "Content-Encoding": "gzip",
                },
                content=compressed,
            )
        )
        real_client = httpx.Client

        def fake_client(*args, **kwargs):
            kwargs["transport"] = transport
            return real_client(*args, **kwargs)

        client = TelegramJWKClient("https://oauth.telegram.org/.well-known/jwks.json")
        with patch("app.utils.jwks.httpx.Client", fake_client):
            self.assertEqual(client.fetch_data(), payload)


if __name__ == "__main__":
    unittest.main()
