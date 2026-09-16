from app.core.errors import NotFoundError
from app.core.exceptions import bad_request_exception, not_found_exception
from app.data.student import StudentDataSQLAlchemy
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


class StudentService:
    def __init__(self, repo: StudentDataSQLAlchemy) -> None:
        self.repo = repo

    async def complete_student(self, user: User, data: StudentComplete) -> UserResponse:
        try:
            user = await self.repo.complete_student(user.id, data)
        except NotFoundError as exc:
            raise not_found_exception(exc.message)
        except ValueError as exc:
            raise bad_request_exception(str(exc))
        return UserResponse.model_validate(user)

    async def edit_student(self, user_id: int, data: StudentUpdate) -> UserResponse:
        try:
            res = await self.repo.edit_student(user_id, data)
        except NotFoundError:
            raise not_found_exception("Student not found")
        if res is None:
            raise not_found_exception("Student not found")
        return res

    async def delete_students(self, ids: StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.DELETED)

    async def recovery_students(self, ids: StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.NOT_CONFIRMED)

    async def confirm_students(self, ids: StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.STUDENT)

    async def unconfirm_students(self, ids: StudentBulkRequest) -> StudentBulkResponse:
        return await self.repo.bulk_role_update(ids, UserRoleEnum.NOT_CONFIRMED)

    async def search(self, data: StudentFilterParams) -> StudentsResponseList:
        return await self.repo.search_students(data)
