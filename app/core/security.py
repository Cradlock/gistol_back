from datetime import datetime, timedelta, timezone
from typing import Dict

from passlib.context import CryptContext

from jose import jwt

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Хеширование пароля (для регистрации / смены пароля)"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Проверка введенного пароля с хешем из базы данных (для логина)"""
    hashed_password = "" if hashed_password is None else hashed_password  
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data : Dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp":expire,"type":"access"})
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data : Dict) -> str:
    to_encode = data.copy() 

    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp":expire,"type":"refresh"})

    return jwt.encode(to_encode,settings.secret_key,algorithm=settings.algorithm)






