




# Сервис для уже "студентов"
#   user - которые прошли полную регистрацию
#


from abc import ABC, abstractmethod


class StudentDataAbstract(ABC):
    

    @abstractmethod 
    async def confirm_student(self,user_id:int):
        pass 


class StudentService:
    pass    





