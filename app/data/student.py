

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
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Запрашиваем обновлённого пользователя вместе с объектом group
        query = (
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.group))
        )
        result = await self.db.execute(query)
        return result.scalar().first()


