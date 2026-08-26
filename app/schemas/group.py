




from datetime import datetime
from enum import StrEnum

from typing_extensions import Optional

from pydantic import BaseModel, Field

from app.models.years import Year

class SortTypeEnum(StrEnum):
    max_to_min = 'max_to_min'
    min_to_max = 'min_to_max'

class SortFieldEnum(StrEnum):
    date = 'date'
    student_count = 'student_count'
    group_title = 'title'


class GroupSearchParams(BaseModel): 
    sort_type: Optional[SortTypeEnum] = Field( description="Тип сортировки (от большего к меньшему (max_to_min) и наоборт (min_to_max) ) ")
    sort_field: Optional[SortFieldEnum] = Field( description="Поле по которому будет идти сортировка ") 
    title: Optional[str] = Field(default=None,description="Название группы")

    min_students_count: Optional[int] = Field(default=None, description="Минимальное число студентов")
    max_students_count: Optional[int] = Field(default=None, description="Максимальное число студентов")

    min_date: Optional[datetime] = Field(default=None, description="Дата от")
    max_date: Optional[datetime] = Field(default=None, description="Дата до")

    min_year: Optional[Year] = Field(default=None, description="Год от")
    max_year: Optional[Year] = Field(default=None, description="Год до")

    active: Optional[bool] = Field(default=None, description="Активна ли группа")
    
    page:int = Field(...,description="Номер порции данных")
    page_size:int = Field(...,description="Количество данных в одной порции")

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
    is_active:bool = Field(
        default=True,
        description="Активность группы"
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
    created_date: datetime 

    class Config:
        # Включаем ORM-режим, чтобы Pydantic умел читать данные прямо из моделей SQLAlchemy
        from_attributes = True

class GroupListResponse(BaseModel):
    total: int
    groups: list[GroupResponse]

