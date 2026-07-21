from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.auth import AuthDataSQLAlchemy
from app.data.groups import GroupDataSQLAlchemy
from app.db import AsyncSessionLocal
from fastapi import Depends, Request
from app.core import * 
from app.models.user import User, UserRoleEnum
from app.core.config import settings
from app.services.auth import AuthService
from app.services.groups import GroupService
# Сессия в дб
async def get_db():
    async with AsyncSessionLocal() as session:
            yield session

# Фабрики репозиториев (все берут одну сессию БД)
def get_auth_repo(db: AsyncSession = Depends(get_db)):
    return AuthDataSQLAlchemy(db)

def get_group_repo(db: AsyncSession = Depends(get_db)):
    return GroupDataSQLAlchemy(db)

def get_group_service(
    repository: GroupDataSQLAlchemy = Depends(get_group_repo)
) -> GroupService:
    return GroupService(repository)


def get_auth_service(
    repository: AuthDataSQLAlchemy = Depends(get_auth_repo)
) -> AuthService:
    return AuthService(repository)

async def get_raw_token(request: Request) -> str: 
    auth_header = request.headers.get('Authorization');
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
        
    token_from_cookie = request.cookies.get("access_token")
    if token_from_cookie:
        return token_from_cookie
        
    raise unauthorized_exception("Token not found") 
 
async def get_refresh_token(request: Request) -> str: 
    auth_header = request.headers.get('Authorization');
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
        
    token_from_cookie = request.cookies.get("refresh_token")
    if token_from_cookie:
        return token_from_cookie
        
    raise unauthorized_exception("Token not found") 
 
async def get_current_user(
    token: str = Depends(get_raw_token),
    service: AuthService = Depends(get_auth_service)
    ) -> User:
    try: 
        payload = jwt.decode(token,settings.secret_key,algorithms=[settings.algorithm]);
        user_id: int | None = payload.get("sub")
        if user_id is None or payload.get("type") == "refresh": # Защита: рефреш-токен нельзя юзать вместо акцесса
            raise unauthorized_exception("Token expired")
    except JWTError:
        raise unauthorized_exception("Invalid token signature or expired") 


    user = await service.get_user_by_id(int(user_id))
    if not user:
        raise unauthorized_exception("User not found")
    return user

async def get_current_student(
    user: User = Depends(get_current_user)
) -> User:
    if user.confirmed:
        return user 
    raise bad_request_exception("User not confirmed")

async def get_current_teacher(
    current_user: User = Depends(get_current_user)  # Твоя текущая зависимость проверки JWT
) -> User:
    # Если токен валидный, но флаг is_admin равен False
    if not current_user.role >= UserRoleEnum.TEACHER:
        raise forbidden_exception(detail="Only admin, have access this action")
    return current_user



