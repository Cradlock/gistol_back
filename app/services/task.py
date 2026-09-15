from datetime import datetime, timezone

from app.core.errors import DuplicateError, NotFoundError
from app.core.exceptions import (
    bad_request_exception,
    conflict_exception,
    forbidden_exception,
    not_found_exception,
)
from app.data.task import TaskDataSQLAlchemy
from app.models.task import SituationsTask, StudentAnswerStatus, StudentAnswerTask
from app.models.user import User
from app.schemas.task import (
    AnswerListResponse,
    AnswerHistoryListResponse,
    AnswerHistoryResponse,
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

    async def list_available_tasks(
        self, user: User, page: int, page_size: int
    ) -> TaskListResponse:
        if user.group_id is None:
            raise bad_request_exception("Student group is not assigned")
        tasks, total = await self.repo.list_available_for_student(
            user_id=user.id,
            group_id=user.group_id,
            now=datetime.now(timezone.utc),
            page=page,
            page_size=page_size,
        )
        return TaskListResponse(
            total=total,
            tasks=[TaskResponse.model_validate(task) for task in tasks],
        )

    async def submit_answer(
        self, task_id: int, user: User, text: str
    ) -> StudentAnswerTask:
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise not_found_exception("Task not found")
        if user.group_id is None:
            raise bad_request_exception("Student group is not assigned")
        if task.group_id != user.group_id:
            raise forbidden_exception("Task belongs to another group")

        now = datetime.now(timezone.utc)
        if now < task.start_at or now >= task.end_at:
            raise bad_request_exception("Task is not available at this time")
        if await self.repo.get_answer_for_user_task(user.id, task_id) is not None:
            raise conflict_exception("Answer already submitted")

        try:
            return await self.repo.create_answer(user.id, task_id, text)
        except DuplicateError:
            raise conflict_exception("Answer already submitted")

    async def get_answer_history(
        self, user: User, page: int, page_size: int
    ) -> AnswerHistoryListResponse:
        answers, total = await self.repo.list_answer_history(
            user.id, page, page_size
        )
        return AnswerHistoryListResponse(
            total=total,
            answers=[
                AnswerHistoryResponse(
                    id=answer.id,
                    task_id=answer.task_id,
                    task_title=answer.task.title,
                    task_content=answer.task.content,
                    task_end_at=answer.task.end_at,
                    points=answer.task.points,
                    text=answer.text,
                    status=answer.status,
                    submitted_at=answer.submitted_at,
                )
                for answer in answers
            ],
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
