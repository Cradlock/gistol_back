from pydantic import BaseModel, EmailStr, Field, computed_field

from app.models.base import Base
from app.models.user import UserRoleEnum
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
    year: int | None = None
    group_id: int | None = None
    group: GroupResponse | None = None
    role: int  

    @computed_field
    @property
    def confirmed(self) -> bool:
        return self.role > UserRoleEnum.NOT_CONFIRMED
    
    @computed_field
    @property
    def deleted(self) -> bool:
        return self.role < UserRoleEnum.DELETED

 
    class Config:
        from_attributes = True


# Telegram logic 
class TelegramAuthRequest(BaseModel):
    id_token: str

class TelegramAuthResponse(BaseModel):
    access_token: str 
    refresh_token: str
    user: UserResponse


# Refres logic 
class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str 

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


class AdminProfileResponse(BaseModel):
    id: int
    code: str | None = None
    name: str | None = None
    surname: str | None = None
    role: int

    class Config:
        from_attributes = True


class AdminCodeUpdateRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=3, max_length=25)


class AdminPasswordUpdateRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

# Complete user logic 
class CompleteUserRequest(BaseModel):
    name: str 
    surname: str 
    group_id: int 
    year: Year



