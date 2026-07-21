



from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.security import hash_password
from app.data.auth import AuthDataSQLAlchemy
from app.models.user import UserRoleEnum
from app.services.auth import AuthService

from app.db import AsyncSessionLocal

async def create_admin(service: AuthService):
    code = settings.root_code
    raw_password = settings.root_password
    
    existing_admin = await service.repository.get_by_field("code", code)
    if existing_admin:
        return 

    admin_data = {
        "code":code,
        "password_hash": hash_password(raw_password),
        "name":"Root admin",
        "role":UserRoleEnum.SUPERADMIN,
        "confirmed": True
    }

    
    await service.repository.create_user(admin_data)
    print(f"Admin: {code} created")


@asynccontextmanager
async def lifespan(app:FastAPI):
    async with AsyncSessionLocal() as session:
        auth_repo = AuthDataSQLAlchemy(session)
        auth_service = AuthService(auth_repo)
        
        # Запускаем создание админа
        await create_admin(auth_service)    
    yield 




