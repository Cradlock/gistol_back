from app.core.errors import NotFoundError
from app.core.exceptions import bad_request_exception, not_found_exception
from app.data.task import TaskDataSQLAlchemy
from app.models.task import SituationsTask, StudentAnswerStatus, StudentAnswerTask
from app.schemas.task import (
    AnswerListResponse,
    AnswerResponse,
    TaskListResponse,
    TaskResponse,
)


class TaskService:
    def __init__(self, repo: TaskDataSQLAlchemy):
        self.repo = repo

    async def create_task(self, data: dict) -> SituationsTask:
        try:
            return await self.repo.create(data)
        except NotFoundError:
            raise not_found_exception("Group not found")

    async def list_tasks(self, group_id: int | None) -> TaskListResponse:
        tasks, total = await self.repo.list_by_group(group_id)
        return TaskListResponse(
            total=total,
            tasks=[TaskResponse.model_validate(task) for task in tasks],
        )

    async def get_task(self, task_id: int) -> SituationsTask:
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise not_found_exception("Task not found")
        return task

    async def update_task(self, task_id: int, update_data: dict) -> SituationsTask:
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise not_found_exception("Task not found")

        if not update_data:
            return task

        start_at = update_data.get("start_at", task.start_at)
        end_at = update_data.get("end_at", task.end_at)
        if end_at <= start_at:
            raise bad_request_exception("Дата конца должна быть позже даты начала")

        try:
            return await self.repo.partial_update(task_id, update_data)
        except NotFoundError as exc:
            raise not_found_exception(exc.message)

    async def delete_task(self, task_id: int) -> None:
        try:
            await self.repo.delete(task_id)
        except NotFoundError:
            raise not_found_exception("Task not found")

    async def list_answers(self, task_id: int) -> AnswerListResponse:
        try:
            answers, total = await self.repo.list_answers(task_id)
        except NotFoundError:
            raise not_found_exception("Task not found")
        return AnswerListResponse(
            total=total,
            answers=[AnswerResponse.model_validate(answer) for answer in answers],
        )

    async def review_answer(
        self, answer_id: int, status: StudentAnswerStatus
    ) -> StudentAnswerTask:
        try:
            return await self.repo.review_answer(answer_id, status)
        except NotFoundError:
            raise not_found_exception("Answer not found")
