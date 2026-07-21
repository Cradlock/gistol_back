




from typing_extensions import Optional

from pydantic import BaseModel, Field

from app.models.years import Year


class GroupCreate(BaseModel):
    title: str = Field(
        ..., 
        min_length=2, 
        max_length=50, 
        examples=["БПИ-231"],
        description="Уникальное название группы"
    )
    year: Year = Field(
        ..., 
        description="Курс, к которому относится группа (число от 1 до 6)"
    )

class GroupUpdate(BaseModel):
    title: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=50, 
        examples=["БПИ-231М"]
    )
    year: Optional[Year] = None

class GroupResponse(BaseModel):
    id: int
    title: str
    year: Year
    is_active: bool

    class Config:
        # Включаем ORM-режим, чтобы Pydantic умел читать данные прямо из моделей SQLAlchemy
        from_attributes = True



