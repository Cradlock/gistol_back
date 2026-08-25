
from datetime import datetime
from operator import index
from typing import final
from sqlalchemy import DateTime, ForeignKey,Enum, String, func
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
    
    created_date: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False
    )   
    
    year: Mapped[Year] = mapped_column(Enum(Year),default=Year.FIRST)

    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    users: Mapped["User"] = relationship(back_populates="group")

