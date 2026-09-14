




# Сервис для уже "студентов"
#   user - которые прошли полную регистрацию
#


from abc import ABC, abstractmethod

from app.core.exceptions import not_found_exception
from app.models.user import User, UserRoleEnum
from app.schemas.auth import UserResponse
from app.schemas.students import StudentBulkRequest, StudentBulkResponse, StudentComplete, StudentFilterParams, StudentUpdate, StudentsResponseList


class StudentDataAbstract(ABC):
    
    @abstractmethod
    async def search_students(self, data: StudentFilterParams) -> StudentsResponseList:
        pass 

   
    @abstractmethod
    async def complete_student(self,user_id,data: StudentComplete)-> User:
        pass

    @abstractmethod
    async def edit_student(self,student_id:int,data: StudentUpdate) -> UserResponse:
        pass
    
    @abstractmethod
    async def bulk_role_update(self,ids: StudentBulkRequest,role: UserRoleEnum) -> StudentBulkResponse:
        pass

class StudentService:
    
    def __init__(self,repo : StudentDataAbstract) -> None:
        self.repo = repo 
    

    async def complete_student(self,user : User,data: StudentComplete)-> UserResponse:
        user =  await self.repo.complete_student(user.id, data); 
        return UserResponse.model_validate(user)

    async def edit_student(self,user_id:int,data:StudentUpdate) -> UserResponse:
        res = await self.edit_student(user_id,data)

        if res is None:
            raise not_found_exception("Student not found")

        return res

    async def delete_students(self,ids: StudentBulkRequest)-> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids,UserRoleEnum.DELETED)
            
    async def recovery_students(self, ids: StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.NOT_CONFIRMED)

    async def confirm_students(self,ids:StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.STUDENT)

    async def unconfirm_students(self,ids:StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids,UserRoleEnum.NOT_CONFIRMED)
    

    
    async def search(self, data: StudentFilterParams) -> StudentsResponseList:
        return await self.repo.search_students(data)
