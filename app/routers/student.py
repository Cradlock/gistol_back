
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse


router = APIRouter(
    prefix="/student",
    tags=["Student"]
)


# Эндпоинты студент - логики



# Проверка пользователя
@router.get("/me",response_model=UserResponse)
async def me_api(current_user : User = Depends(get_current_user)):
    return current_user





#
# Логика для админа


## Изменения студента 
@router.patch("/{user_id}",response_model=UserResponse)
async def student_patch(
        user_id:int 
):
    pass 






