from enum import Enum
from operator import index
from typing import final
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.years import Year
   
@final
class Group(Base):
    __tablename__ = "groups"
    """
    Это ГРУППЫ 
    """
    id: Mapped[int] = mapped_column(primary_key=True)
    
    title: Mapped[str] = mapped_column(String(100),unique=True) 
    
    year: Mapped[Year] = mapped_column(Enum(Year),default=Year.FIRST)

    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    users: Mapped["User"] = relationship(back_populates="group")

