

from typing import override

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

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
    async def complete_student(self, user_id: int, data: StudentComplete) -> User:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                name=data.name,
                surname=data.surname,
                group_id=data.group_id
            )
            .returning(User)
        )
        result = await self.db.execute(stmt)
        updated_user = result.scalars().first()
        
        await self.db.commit()
        
        # Подгружаем атрибуты/связи объекта
        await self.db.refresh(updated_user, attribute_names=['group'])
        if updated_user is None:
            raise Exception()

        return updated_user
