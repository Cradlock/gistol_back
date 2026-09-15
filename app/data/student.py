from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import NotFoundError
from app.data.common import handle_integrity_error
from app.models.user import User, UserRoleEnum
from app.schemas.auth import UserResponse
from app.schemas.students import (
    StudentBulkRequest,
    StudentBulkResponse,
    StudentComplete,
    StudentFilterParams,
    StudentUpdate,
    StudentsResponseList,
)


class StudentDataSQLAlchemy:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_students(self, data: StudentFilterParams) -> StudentsResponseList:
        stmt = select(User).options(joinedload(User.group))
        conditions = []

        roles_to_include = []
        if data.deleted:
            roles_to_include.append(UserRoleEnum.DELETED)
        else:
            roles_to_include.append(UserRoleEnum.STUDENT)
            if not data.confirmed:
                roles_to_include.append(UserRoleEnum.NOT_CONFIRMED)

        conditions.append(User.role.in_(roles_to_include))

        if data.group_id is not None:
            conditions.append(User.group_id == data.group_id)

        if data.fio:
            conditions.append(User.fio.ilike(f"%{data.fio.strip()}%"))

        if data.min_year is not None:
            conditions.append(User.year >= data.min_year)
        if data.max_year is not None:
            conditions.append(User.year <= data.max_year)

        stmt = stmt.where(*conditions)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = getattr(User, data.sort_field, User.year)
        if data.sort_type in ("max_to_min", "desc"):
            sort_column = sort_column.desc()
        else:
            sort_column = sort_column.asc()

        stmt = stmt.order_by(sort_column)
        offset = (data.page - 1) * data.page_size
        stmt = stmt.offset(offset).limit(data.page_size)

        result = await self.db.execute(stmt)
        users = result.scalars().unique().all()

        return StudentsResponseList(
            students=[UserResponse.model_validate(user) for user in users],
            total=total,
        )

    @handle_integrity_error
    async def complete_student(self, user_id: int, data: StudentComplete) -> User:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                name=data.name,
                surname=data.surname,
                group_id=data.group_id,
            )
            .returning(User)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        updated_user = result.scalars().first()
        if updated_user is None:
            raise NotFoundError("Student not found")
        return updated_user

    @handle_integrity_error
    async def edit_student(self, student_id: int, data: StudentUpdate) -> UserResponse:
        stmt = (
            update(User)
            .where(User.id == student_id)
            .values(**data.model_dump(exclude_unset=True))
            .returning(User.id)
        )
        result = await self.db.execute(stmt)
        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            await self.db.rollback()
            raise NotFoundError("Student not found")

        await self.db.commit()
        loaded = await self.db.execute(
            select(User)
            .options(joinedload(User.group))
            .where(User.id == updated_id)
        )
        updated_user = loaded.unique().scalar_one()
        return UserResponse.model_validate(updated_user)

    @handle_integrity_error
    async def bulk_role_update(
        self,
        request: StudentBulkRequest,
        role: UserRoleEnum,
    ) -> StudentBulkResponse:
        req_ids = request.ids

        if not req_ids:
            return StudentBulkResponse(completed=[], faileds=[])

        stmt = (
            update(User)
            .where(User.id.in_(req_ids))
            .values(role=role)
            .returning(User.id)
        )
        result = await self.db.execute(stmt)
        updated_ids = list(result.scalars().all())
        updated_set = set(updated_ids)
        faileds = [student_id for student_id in req_ids if student_id not in updated_set]

        await self.db.commit()
        return StudentBulkResponse(completed=updated_ids, faileds=faileds)
