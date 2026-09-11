from abc import ABC, abstractmethod
from jwt import (
    PyJWKClient, PyJWKSet, PyJWTError, get_unverified_header
)
import jwt
from sqlalchemy import except_
from app.core import settings,verify_password
from fastapi import Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Any, Optional

# Импортируем твои кастомные исключения напрямую
from app.core import (
    unauthorized_exception,
    bad_request_exception,
    forbidden_exception,
    not_found_exception,
    conflict_exception,
    validation_exception,
    internal_server_exception
)
import httpx

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User, UserRoleEnum


class AuthDataAbstract(ABC):
    # --- ЧТЕНИЕ (READ) ---
    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по первичному ключу (ID)"""
        pass
    
    @abstractmethod
    async def get_all_by_field(self, field: str, value: Any) -> list[User]:
        """Универсальный метод получения СПИСКА пользователей по полю (например, group_id)"""
        pass
    
    @abstractmethod
    async def get_by_field(self, field: str, value: Any) -> User | None:
        """
        Универсальный метод поиска. 
        Например: get_by_field("telegram_id", "123456")
        """
        pass

    # --- ЗАПИСЬ И ОБНОВЛЕНИЕ (WRITE & UPDATE) ---
    @abstractmethod
    async def create_user(self, user_data: dict) -> User:
        """Создать нового пользователя в БД"""
        pass

    @abstractmethod
    async def update_user(self, user_id: int, update_data: dict) -> User | None:
        """Обновить данные пользователя"""
        pass

    # --- УТИЛИТЫ (UTILITY) ---
    @abstractmethod
    async def exists_by_field(self, val_id, field: str = "telegram_id") -> bool:
        """Быстрая проверка существования записи"""
        pass



class AuthService:
    
    def __init__(self, auth_repository: AuthDataAbstract):
        if auth_repository is None:
            raise ValueError("AuthService требует валидный auth_repository")
        self.repository = auth_repository
        self.bot_client_id = settings.telegram_bot_client_id
        self.TELEGRAM_ISSUER = "https://oauth.telegram.org"
        self.TELEGRAM_JWKS_URL = (
            "https://oauth.telegram.org/.well-known/jwks.json"
        )

        self._jwks_client = PyJWKClient(
            self.TELEGRAM_JWKS_URL, cache_keys=True
        )

    async def verify_telegram_token(self, id_token: str) -> dict:
        try:
            # PyJWKClient заглядывает в кэш; если ключа нет — делает один HTTP-запрос и сохраняет его
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
            # Ошибки получения ключей или соединения с Telegram
            raise internal_server_exception(
                f"Failed to verify Telegram auth: {str(e)}"
            )

    async def get_telegram_user(self, id_token: str) -> dict:
        payload = await self.verify_telegram_token(id_token)

        telegram_id = str(payload.get("id") or payload.get("sub"))

        user = await self.repository.get_by_field("telegram_id", telegram_id)

        if user is None:
            user = await self.repository.create_user(
                {"telegram_id": telegram_id}
            )

        token_payload = {"sub": str(user.id)}

        return {
            "user": user,
            "access_token": create_access_token(token_payload),
            "refresh_token": create_refresh_token(token_payload),
        }    async def login_by_code(self, code: str, password: str) -> dict:
        user = await self.repository.get_by_field("code", code)
        
        if not user or user.role < UserRoleEnum.TEACHER:
            raise unauthorized_exception("Incorrect password or code")
            
        # Здесь будет твоя функция проверки хэша пароля (например, verify_password)
        if not verify_password(password, user.password_hash):
            raise unauthorized_exception("Incorrect password or code ")
        
        payload = {
            "sub": str(user.id)
        }

        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "user": user,
        }
    
    async def refresh_token(self,payload: dict) -> dict:
        # Проверьте, что payload вообще содержит 'sub' перед тем как к нему обращаться
        if "sub" not in payload:
            raise unauthorized_exception("Invalid refresh token") 
        token_payload = {
            "sub": str(payload["sub"])
        }
        
        return {
            "access_token": create_access_token(token_payload),
            "refresh_token": create_refresh_token(token_payload)
        }


    async def get_user_by_id(self, id: int) -> User | None:
        return await self.repository.get_by_id(id)
     

    async def complete_student_profile(self, user: User,data:dict) -> User:
        data['confirmed'] = True    
    
        updated_user = await self.repository.update_user(user.id,data)
        
        if not updated_user:
            raise not_found_exception("Пользователь не найден")
        
        return updated_user


    # На будущее 
    # async def create_teacher(self, code,password ):
    #    pass 
    
    async def get_students_by_group(self,group_id:int) -> list[User]:
        users = await self.repository.get_all_by_field("group_id",group_id)
        
        return users
    
    
    




