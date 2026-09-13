from datetime import datetime
from enum import IntEnum, unique
from operator import index
from typing import Optional, final
from httpx._transports import default
from pydantic import EmailStr
from sqlalchemy import Computed, Enum,BigInteger, CheckConstraint, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

from app.models.groups import Group
from app.models.years import Year


class UserRoleEnum(IntEnum):
    DELETED = 1
    NOT_CONFIRMED = 3
    STUDENT = 5
    TEACHER = 20
    SUPERADMIN = 999


@final
class User(Base):
    __tablename__ = "users"
    
    role: Mapped[UserRoleEnum] = mapped_column(Integer, default=UserRoleEnum.NOT_CONFIRMED,index=True) 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    surname: Mapped[Optional[str]] = mapped_column(String(50))
    
    # вход для админа 
    code: Mapped[Optional[str]] = mapped_column(String(25),unique=True,nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255),nullable=True)

    # Вход через телеграм
    telegram_id: Mapped[Optional[str]] = mapped_column(String(255),unique=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(255))

    # Вход через Google 
    google_id : Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    email:  Mapped[Optional[str]] = mapped_column(String(255), unique=True) 

    scores: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
     

    # Это связь FroegnKey  
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("groups.id"))
    year: Mapped[Optional[Year]] = mapped_column(Enum(Year),default=Year.FIRST)
 
    # Это relationship,тут же все понятно зачем чето еще писать
    group: Mapped["Group"] = relationship(back_populates="users")
     
    # Виртуальная колонка   
    fio: Mapped[str] = mapped_column(
        String(105), 
        Computed("name || ' ' || surname", persisted=True)
    )      
    __table_args__ = (
        CheckConstraint(
            "telegram_id IS NOT NULL OR google_id IS NOT NULL OR code IS NOT NULL",
            name="check_at_least_one_auth_method",
        ),   
        Index(  
            "idx_users_fio_trgm",
            "fio", 
            postgresql_ops={"fio": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )  
 
 
