



from fastapi import APIRouter, Depends, status
from sqlalchemy.sql.visitors import prefix_anon_map

from app.models.years import Year 
from app.schemas.year import YearsResponse


router = APIRouter(
    prefix="/years",
    tags=["Years"] 
)

@router.get("/", response_model=YearsResponse)
async def get_available_years():
    """Возвращает список всех существующих курсов для фронтенда"""
    return {"years":list(Year)} 
