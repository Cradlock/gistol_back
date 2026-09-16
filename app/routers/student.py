
from fastapi import APIRouter, Depends

from app.dependencies import get_auth_service, get_current_teacher, get_current_user, get_student_repo, get_student_service
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.students import StudentBulkRequest, StudentBulkResponse, StudentComplete, StudentFilterParams, StudentUpdate, StudentsResponseList
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
    return UserResponse.model_validate(current_user)


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
@router.patch("/{user_id}", response_model=UserResponse)
async def student_patch(
    user_id: int,
    data: StudentUpdate,
    admin: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
):
    return await service.edit_student(user_id, data) 

@router.post("/confirm",response_model=StudentBulkResponse)
async def confirm_students(
        ids: StudentBulkRequest,
        admin: User = Depends(get_current_teacher),
        service: StudentService = Depends(get_student_service),
        ):
    return await service.confirm_students(ids)

@router.post("/unconfirm",response_model=StudentBulkResponse)
async def unconfirm_students(
        ids: StudentBulkRequest,
        admin: User = Depends(get_current_teacher),
        service: StudentService = Depends(get_student_service),
        ):
    return await service.unconfirm_students(ids)



@router.delete("/delete",response_model=StudentBulkResponse)
async def delete_students(
        ids: StudentBulkRequest,  
        admin: User = Depends(get_current_teacher),
        service: StudentService = Depends(get_student_service),
):
    return  await service.delete_students(ids)

@router.post("/recovery",response_model=StudentBulkResponse)
async def recovery_students(
        ids: StudentBulkRequest,
        admin: User = Depends(get_current_teacher),
        service: StudentService = Depends(get_student_service),
 
):
    return  await service.recovery_students(ids)




## Поиск студента
@router.get("/search",response_model=StudentsResponseList)
async def student_search(
    admin: User = Depends(get_current_teacher),
    service: StudentService = Depends(get_student_service),
    data: StudentFilterParams = Depends()
):
    return await service.search(data) 



