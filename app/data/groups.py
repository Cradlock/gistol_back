from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.data.common import handle_integrity_error
from app.models.groups import Group
from app.models.years import Year
from app.schemas.group import GroupSearchParams, SortTypeEnum


class GroupDataSQLAlchemy:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_year(self, year: Year) -> tuple[list[Group], int]:
        query = (
            select(Group)
            .where(Group.year == year, Group.is_active == True)
            .order_by(Group.title)
        )
        result = await self.db.execute(query)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        return list(result.scalars().all()), total

    @handle_integrity_error
    async def bulk_return(self, group_ids: list[int]) -> int:
        query = (
            update(Group)
            .where(Group.id.in_(group_ids))
            .values(is_active=True)
            .returning(Group.id)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return len(result.scalars().all())

    @handle_integrity_error
    async def bulk_soft_delete(self, group_ids: list[int]) -> int:
        query = (
            update(Group)
            .where(Group.id.in_(group_ids))
            .values(is_active=False)
            .returning(Group.id)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return len(result.scalars().all())

    @handle_integrity_error
    async def create(self, data: dict) -> Group:
        new_group = Group(**data)
        self.db.add(new_group)
        await self.db.commit()
        await self.db.refresh(new_group)
        return new_group

    async def search(self, params: GroupSearchParams) -> tuple[list[Group], int]:
        query = select(Group)
        filters = []

        if params.title:
            filters.append(Group.title.ilike(f"%{params.title}%"))

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
            query = query.where(*filters)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        if params.sort_field and params.sort_type:
            column = getattr(Group, params.sort_field.value, Group.created_date)
            if params.sort_type == SortTypeEnum.max_to_min:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        result = await self.db.execute(query)
        groups = result.scalars().all()
        return list(groups), total

    @handle_integrity_error
    async def partial_update(self, id: int, update_data: dict) -> Optional[Group]:
        query = (
            update(Group)
            .where(Group.id == id)
            .values(**update_data)
            .returning(Group)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        group = result.scalar_one_or_none()
        if group is None:
            raise NotFoundError("Group not found")
        return group

    async def get_by_id(self, id: int) -> Group | None:
        query = select(Group).where(Group.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
