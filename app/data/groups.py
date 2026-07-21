



from typing import Optional, Sequence, override

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.groups import Group
from app.models.years import Year
from app.services.groups import GroupDataAsbtract


class GroupDataSQLAlchemy(GroupDataAsbtract):

    def __init__(self, db: AsyncSession):
        self.db = db
    
   
    @override
    async def get_active_by_year(self, year: Year) -> Sequence[Group]:
        """Фильтрация живых групп по конкретному курсу (для фронтенда регистраций)"""
        query = select(Group).where(Group.year == year, Group.is_active == True).order_by(Group.title)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    @override
    async def create(self, data: dict) -> Group:
        new_group = Group(**data)
        self.db.add(new_group)
        await self.db.commit()
        await self.db.refresh(new_group)
        return new_group
    
    @override
    async def partial_update(self,id: int, update_data: dict) -> Optional[Group]:
        query = (
            update(Group)
            .where(Group.id == id)
            .values(**update_data)
            .returning(Group)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()

    @override
    async def get_by_id(self, id: int) -> Group | None:
        query = select(Group).where(Group.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() 

