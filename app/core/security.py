from datetime import datetime, timedelta, timezone
from typing import Dict


from jose import jwt

from app.core.config import settings


import bcrypt

def hash_password(password: str) -> str:
    # Конвертируем в байты, обрезаем на всякий случай до 72 байт (ограничение bcrypt)
    pwd_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    pwd_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))

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






