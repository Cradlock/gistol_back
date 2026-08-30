




from pydantic import BaseModel

from app.models.years import Year


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

