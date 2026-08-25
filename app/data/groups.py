



from operator import and_
from typing import Optional, Sequence, override

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.groups import Group
from app.models.years import Year
from app.schemas.group import GroupSearchParams, SortTypeEnum
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
    async def search(self, params: GroupSearchParams) -> tuple[list[Group], int]:
        # Базовый запрос к таблице групп (предположим, модель SQLAlchemy называется GroupModel)
        query = select(Group)
        
        # 1. Применяем фильтры (динамический WHERE)
        filters = []
        
        if params.title:
            # Поиск по подстроке (ILIKE для регистронезависимости в Postgres)
            filters.append(Group.title.ilike(f"%{params.title}%"))
            
        if params.active is not None:
            filters.append(Group.is_active == params.active)
            
        if params.min_year:
            filters.append(Group.year >= params.min_year)
            
        if params.max_year:
            filters.append(Group.year <= params.max_year)
            
        if params.min_date:
            filters.append(Group.created_date >= params.min_date)
            
        if params.max_date:
            filters.append(Group.created_date <= params.max_date)
            
        if filters:
            query = query.where(and_(*filters))

        # 2. Считаем общее количество записей (для пагинации и hasNext)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # 3. Применяем сортировку (ORDER BY)
        if params.sort_field and params.sort_type:
            column = getattr(Group, params.sort_field.value, Group.created_date)
            if params.sort_type == SortTypeEnum.max_to_min:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        # 4. Применяем пагинацию (LIMIT / OFFSET)
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        # 5. Выполняем запрос
        result = await self.db.execute(query)

        groups = result.scalars().all()

        return list(groups), total


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

