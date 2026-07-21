from pydantic import BaseModel, EmailStr, Field

from app.models.base import Base
from app.models.years import Year
from app.schemas.group import GroupResponse


# User logic 
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    surname: str = Field(..., min_length=2, max_length=50)
    password: str = Field(...)
    year_id: int
    group_id: int


class UserResponse(BaseModel):
    id: int
    name: str
    surname: str
    scores: int
    year: int 
    group: GroupResponse

    class Config:
        from_attributes = True


# Telegram logic 
class TelegramAuthRequest(BaseModel):
    id_token: str

class TelegramAuthResponse(BaseModel):
    access: str 
    refresh: str
    isNew: bool
    telegramId: str
    user: UserResponse | None



# Refres logic 
class RefreshTokenResponse(BaseModel):
    access: str 

class RefreshTokenRequest(BaseModel):
    refresh: str 




# Admin logic  
class AdminLoginRequest(BaseModel):
    code:str 
    password:str

class AdminLoginResponse(BaseModel):
    access: str 
    refresh: str 
    user: UserResponse

# Complete user logic 
class CompleteUserRequest(BaseModel):
    name: str 
    surname: str 
    group_id: int 
    year: Year



