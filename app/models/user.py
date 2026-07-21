from datetime import datetime
from enum import Enum, IntEnum, unique
from operator import index
from typing import Optional, final
from httpx._transports import default
from pydantic import EmailStr
from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

from app.models.groups import Group
from app.models.years import Year


class UserRoleEnum(IntEnum):
    STUDENT = 1
    TEACHER = 20
    SUPERADMIN = 999


@final
class User(Base):
    __tablename__ = "users"
    
    role: Mapped[UserRoleEnum] = mapped_column(Integer, default=UserRoleEnum.STUDENT,index=True) 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    surname: Mapped[Optional[str]] = mapped_column(String(50))
    
    # вход для админа 
    code: Mapped[Optional[str]] = mapped_column(String(25),unique=True,nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255),nullable=True)

    # Вход через телеграм
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger,unique=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255))

    # Вход через Google 
    google_id : Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    email:  Mapped[Optional[str]] = mapped_column(String(255), unique=True) 

    scores: Mapped[int] = mapped_column(default=0)

    confirmed: Mapped[bool] = mapped_column(default=False,index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now()) 
      
    # Завершенность записи
    confirmed: Mapped[bool] = mapped_column(default=False)
    
    # Это связь FroegnKey 
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))  
    year: Mapped[Optional[Year]] = mapped_column(Enum(Year),default=Year.FIRST)
    
    # Это relationship,тут же все понятно зачем чето еще писать
    group: Mapped["Group"] = relationship(back_populates="users")



    __table_args__ = (
        CheckConstraint(
            "telegram_id IS NOT NULL OR google_id IS NOT NULL OR code IS NOT NULL",
            name="check_at_least_one_auth_method"
        ),
    )





