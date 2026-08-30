

from typing import override

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.students import StudentComplete
from app.services.student import StudentDataAbstract


class StudentDataSQLAlchemy(StudentDataAbstract):
    
    def __init__(self,db:AsyncSession) -> None:
        self.db = db 


    @override
    async def confirm_student(self, user_id: int):
        return await super().confirm_student(user_id)

    @override
    async def complete_student(self,user_id:int, data: StudentComplete) -> User:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                name=data.name,
                surname=data.surname,
                group_id=data.group_id,
                is_profile_completed=True
            )
            .returning(User) # Возвращаем обновленный объект модели
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        updated_user = result.scalars().first()
        
        return updated_user
