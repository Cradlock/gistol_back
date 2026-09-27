import jwt
from jwt import PyJWTError

from app.utils.jwks import TelegramJWKClient

from app.core import settings, verify_password, hash_password
from app.core import (
    unauthorized_exception,
    forbidden_exception,
    not_found_exception,
    internal_server_exception,
    conflict_exception,
    bad_request_exception,
)
from app.schemas.auth import AdminCodeUpdateRequest, AdminPasswordUpdateRequest
from app.core.errors import DuplicateError
from app.core.security import create_access_token, create_refresh_token
from app.data.auth import AuthDataSQLAlchemy
from app.models.user import User, UserRoleEnum


class AuthService:
    def __init__(self, auth_repository: AuthDataSQLAlchemy):
        self.repository = auth_repository
        self.bot_client_id = settings.telegram_bot_client_id
        self.TELEGRAM_ISSUER = "https://oauth.telegram.org"
        self.TELEGRAM_JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
        self._jwks_client = TelegramJWKClient(
            self.TELEGRAM_JWKS_URL,
            cache_keys=True,
        )

    async def verify_telegram_token(self, id_token: str) -> dict:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.bot_client_id,
                issuer=self.TELEGRAM_ISSUER,
                options={"verify_signature": True, "verify_exp": True},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise unauthorized_exception("Token has expired")
        except PyJWTError as e:
            raise unauthorized_exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise internal_server_exception(
                f"Failed to verify Telegram auth: {str(e)}"
            )

    async def get_telegram_user(self, id_token: str) -> dict:
        payload = await self.verify_telegram_token(id_token)
        telegram_id = str(payload.get("id") or payload.get("sub") or "")
        if not telegram_id:
            raise unauthorized_exception("Telegram user id is missing")

        user = await self.repository.get_by_field("telegram_id", telegram_id)
        if user is None:
            username = payload.get("username")
            create_data: dict = {"telegram_id": telegram_id}
            if isinstance(username, str) and username:
                create_data["telegram_username"] = username
            try:
                user = await self.repository.create_user(create_data)
            except DuplicateError:
                user = await self.repository.get_by_field("telegram_id", telegram_id)
                if user is None:
                    raise
        if user is None:
            raise internal_server_exception("Failed to create Telegram user")
        if user.deleted:
            raise forbidden_exception("Account was deleted ")

        token_payload = {"sub": str(user.id)}
        return {
            "user": user,
            "access_token": create_access_token(token_payload),
            "refresh_token": create_refresh_token(token_payload),
        }

    async def login_by_code(self, code: str, password: str) -> dict:
        user = await self.repository.get_by_field("code", code)

        if not user or user.role < UserRoleEnum.TEACHER:
            raise unauthorized_exception("Incorrect password or code")

        if not verify_password(password, user.password_hash):
            raise unauthorized_exception("Incorrect password or code ")

        payload = {"sub": str(user.id)}
        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "user": user,
        }

    async def refresh_token(self, payload: dict) -> dict:
        if "sub" not in payload:
            raise unauthorized_exception("Invalid refresh token")

        token_payload = {"sub": str(payload["sub"])}
        return {
            "access_token": create_access_token(token_payload),
            "refresh_token": create_refresh_token(token_payload),
        }

    async def get_user_by_id(self, id: int) -> User | None:
        return await self.repository.get_by_id(id)

    async def complete_student_profile(self, user: User, data: dict) -> User:
        data["confirmed"] = True
        updated_user = await self.repository.update_user(user.id, data)
        if not updated_user:
            raise not_found_exception("Пользователь не найден")
        return updated_user

    async def get_students_by_group(self, group_id: int) -> list[User]:
        return await self.repository.get_all_by_field("group_id", group_id)

    def _require_teacher_password(self, user: User, password: str) -> None:
        if user.role < UserRoleEnum.TEACHER:
            raise forbidden_exception("Only admin have access this action")
        if not user.password_hash or not verify_password(password, user.password_hash):
            raise unauthorized_exception("Incorrect password or code")

    async def update_admin_code(
        self, user: User, data: AdminCodeUpdateRequest
    ) -> User:
        self._require_teacher_password(user, data.current_password)
        new_code = data.code.strip()
        if not new_code:
            raise bad_request_exception("Login cannot be empty")

        if user.code != new_code:
            existing = await self.repository.get_by_field("code", new_code)
            if existing is not None and existing.id != user.id:
                raise conflict_exception("Login is already taken")
            try:
                updated = await self.repository.update_user(user.id, {"code": new_code})
            except DuplicateError:
                raise conflict_exception("Login is already taken")
            if updated is None:
                raise not_found_exception("User not found")
            loaded = await self.repository.get_by_id(user.id)
            return loaded or updated
        return user

    async def update_admin_password(
        self, user: User, data: AdminPasswordUpdateRequest
    ) -> User:
        self._require_teacher_password(user, data.current_password)
        updated = await self.repository.update_user(
            user.id,
            {"password_hash": hash_password(data.new_password)},
        )
        if updated is None:
            raise not_found_exception("User not found")
        loaded = await self.repository.get_by_id(user.id)
        return loaded or updated
