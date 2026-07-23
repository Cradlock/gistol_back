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
    name: str | None 
    surname: str | None 
    scores: int | None 
    year: int | None 
    group: GroupResponse | None
    code: str | None

    class Config:
        from_attributes = True


# Telegram logic 
class TelegramAuthRequest(BaseModel):
    id_token: str

class TelegramAuthResponse(BaseModel):
    access_token: str 
    refresh_token: str
    isNew: bool
    telegramId: str
    user: UserResponse | None



# Refres logic 
class RefreshTokenResponse(BaseModel):
    access_token: str 

class RefreshTokenRequest(BaseModel):
    refresh_token: str 




# Admin logic  
class AdminLoginRequest(BaseModel):
    code:str 
    password:str

class AdminLoginResponse(BaseModel):
    access_token: str 
    refresh_token: str 
    user: UserResponse

# Complete user logic 
class CompleteUserRequest(BaseModel):
    name: str 
    surname: str 
    group_id: int 
    year: Year



