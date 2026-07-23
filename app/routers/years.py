



from fastapi import APIRouter, Depends, status
from sqlalchemy.sql.visitors import prefix_anon_map

from app.models.years import Year


router = APIRouter(
    prefix="/years",
    tags=["Years"] 
)

@router.get("/", response_model=dict[int, str])
async def get_available_years():
    """Возвращает список всех существующих курсов для фронтенда"""
    return {
        Year.FIRST.value: "1 курс",
        Year.SECOND.value: "2 курс",
        Year.THIRD.value: "3 курс",
        Year.FOURTH.value: "4 курс",
        Year.FIFTH.value: "5 курс",
        Year.SIXTH.value: "6 курс",
        Year.SIXTH.value: "6 курс",
    }
