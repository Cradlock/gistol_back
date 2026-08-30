




# Сервис для уже "студентов"
#   user - которые прошли полную регистрацию
#


from abc import ABC, abstractmethod

from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.students import StudentComplete


class StudentDataAbstract(ABC):
    

    @abstractmethod 
    async def confirm_student(self,user_id:int):
        pass 
    
    @abstractmethod
    async def complete_student(self,user_id,data: StudentComplete)-> User:
        pass

class StudentService:
    
    def __init__(self,repo : StudentDataAbstract) -> None:
        self.repo = repo 
    

    async def complete_student(self,user : User,data: StudentComplete)-> UserResponse:
        user =  await self.repo.complete_student(user.id, data); 
        return UserResponse.model_validate(user)
