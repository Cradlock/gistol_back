

from typing import override

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.user import User, UserRoleEnum
from app.schemas.auth import UserResponse
from app.schemas.students import StudentComplete, StudentFilterParams, StudentsResponseList
from app.services.student import StudentDataAbstract
import math 

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


    @override
    async def search_students(self, data: StudentFilterParams) -> StudentsResponseList:
        # Базовый запрос
        stmt = select(User).options(joinedload(User.group))
        conditions = []
    
        # 1. Фильтрация по статусам (UserRoleEnum)
        roles_to_include = []
        if data.deleted:
            roles_to_include.append(UserRoleEnum.DELETED)
        else:
            roles_to_include.append(UserRoleEnum.STUDENT)
            if not data.confirmed:
                roles_to_include.append(UserRoleEnum.NOT_CONFIRMED)
    
        conditions.append(User.role.in_(roles_to_include))
    
        # 2. Фильтрация по группе
        if data.group_id is not None:
            conditions.append(User.group_id == data.group_id)
    
        # 3. Поиск по ФИО через сгенерированную колонку / GIN-индекс
        if data.fio:
            conditions.append(User.fio.ilike(f"%{data.fio.strip()}%"))
    
        # 4. Фильтрация по диапазону курсов
        if data.min_year is not None:
            conditions.append(User.year >= data.min_year)
        if data.max_year is not None:
            conditions.append(User.year <= data.max_year)
    
        # Применяем все накопленные условия
        stmt = stmt.where(*conditions)
    
        # 5. Подсчет общего количества записей (Total Count) до пагинации
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()
    
        # 6. Сортировка
        sort_column = getattr(User, data.sort_field, User.year)
        if data.sort_type in ("max_to_min", "desc"):
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()
        
        stmt = stmt.order_by(sort_column)
    
        # 7. Пагинация (Limit / Offset)
        offset = (data.page - 1) * data.page_size
        stmt = stmt.offset(offset).limit(data.page_size)
    
        # 8. Выполнение запроса
        result = await self.db.execute(stmt)
        users = result.scalars().unique().all()
    
        return StudentsResponseList(
            students=[UserResponse.model_validate(user) for user in users],
            total=total
        )
