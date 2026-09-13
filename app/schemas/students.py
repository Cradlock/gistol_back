




from pydantic import BaseModel, Field

from app.models.years import Year
from app.schemas.auth import UserResponse


class StudentUpdate(BaseModel):
    surname: str 
    name: str 
    group_id: int 
    year: Year
    scores: int 
     

class StudentComplete(BaseModel):
    surname: str 
    name:str
    group_id:int 
    year:Year

class StudentFilterParams(BaseModel):
    fio: str | None = None
    min_year: int | None = None
    max_year: int | None = None
    group_id: int | None = None
    confirmed: bool = True   # По умолчанию показываем только подтвержденных
    deleted: bool = False    # По умолчанию НЕ показываем удаленных
    sort_field: str = "year"
    sort_type: str = "min_to_max"

    page:int = Field(...,description="Номер порции данных")
    page_size:int = Field(...,description="Количество данных в одной порции")





class StudentsResponseList(BaseModel):
    total: int
    students: list[UserResponse]



