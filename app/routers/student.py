
from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service, get_current_user, get_student_repo, get_student_service
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.students import StudentComplete
from app.services.auth import AuthService
from app.services.student import StudentService


router = APIRouter(
    prefix="/student",
    tags=["Student"]
)


# Эндпоинты студент - логики



# Проверка пользователя
@router.get("/me",response_model=UserResponse)
async def me_api(current_user : User = Depends(get_current_user)):
    return current_user


# Полнове оформление аккаунта
@router.post("/complete", response_model=UserResponse)
async def complete_student(
    data: StudentComplete, 
    current_user: User = Depends(get_current_user),
    service: StudentService = Depends(get_student_service)
):
    return await service.complete_student(current_user,data)


#
# Логика для админа


## Изменения студента 
@router.patch("/{user_id}",response_model=UserResponse)
async def student_patch(
        user_id:int 
):
    pass 






