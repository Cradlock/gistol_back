from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.data.common import handle_integrity_error
from app.models.groups import Group
from app.models.task import SituationsTask, StudentAnswerStatus, StudentAnswerTask
from app.models.user import User


class TaskDataSQLAlchemy:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: int) -> SituationsTask | None:
        query = select(SituationsTask).where(SituationsTask.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_group(self, group_id: int | None) -> tuple[list[SituationsTask], int]:
        query = select(SituationsTask)
        if group_id is not None:
            query = query.where(SituationsTask.group_id == group_id)
        query = query.order_by(SituationsTask.start_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        tasks = list((await self.db.execute(query)).scalars().all())
        return tasks, total

    async def list_available_for_student(
        self,
        user_id: int,
        group_id: int,
        now: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[SituationsTask], int]:
        already_answered = (
            select(StudentAnswerTask.id)
            .where(
                StudentAnswerTask.task_id == SituationsTask.id,
                StudentAnswerTask.user_id == user_id,
            )
            .exists()
        )
        base_query = select(SituationsTask).where(
            SituationsTask.group_id == group_id,
            SituationsTask.start_at <= now,
            SituationsTask.end_at > now,
            ~already_answered,
        )
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        query = (
            base_query.order_by(SituationsTask.end_at.asc(), SituationsTask.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        tasks = list((await self.db.execute(query)).scalars().all())
        return tasks, total

    async def _ensure_group(self, group_id: int) -> None:
        group = await self.db.get(Group, group_id)
        if group is None:
            raise NotFoundError("Group not found")

    @handle_integrity_error
    async def create(self, data: dict) -> SituationsTask:
        await self._ensure_group(data["group_id"])
        task = SituationsTask(**data)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    @handle_integrity_error
    async def partial_update(self, task_id: int, update_data: dict) -> SituationsTask:
        if "group_id" in update_data:
            await self._ensure_group(update_data["group_id"])

        query = (
            update(SituationsTask)
            .where(SituationsTask.id == task_id)
            .values(**update_data)
            .returning(SituationsTask)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Task not found")
        return task

    @handle_integrity_error
    async def delete(self, task_id: int) -> None:
        result = await self.db.execute(
            delete(SituationsTask).where(SituationsTask.id == task_id)
        )
        if result.rowcount == 0:
            raise NotFoundError("Task not found")
        await self.db.commit()

    async def list_answers(self, task_id: int) -> tuple[list[StudentAnswerTask], int]:
        task = await self.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")

        query = (
            select(StudentAnswerTask)
            .where(StudentAnswerTask.task_id == task_id)
            .order_by(StudentAnswerTask.id)
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        answers = list((await self.db.execute(query)).scalars().all())
        return answers, total

    async def get_answer(self, answer_id: int) -> StudentAnswerTask | None:
        query = (
            select(StudentAnswerTask)
            .options(selectinload(StudentAnswerTask.task))
            .where(StudentAnswerTask.id == answer_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_answer_for_user_task(
        self, user_id: int, task_id: int
    ) -> StudentAnswerTask | None:
        query = select(StudentAnswerTask).where(
            StudentAnswerTask.user_id == user_id,
            StudentAnswerTask.task_id == task_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @handle_integrity_error
    async def create_answer(
        self, user_id: int, task_id: int, text: str
    ) -> StudentAnswerTask:
        answer = StudentAnswerTask(
            user_id=user_id,
            task_id=task_id,
            text=text,
            status=StudentAnswerStatus.PENDING,
        )
        self.db.add(answer)
        await self.db.commit()
        await self.db.refresh(answer)
        return answer

    async def list_answer_history(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[StudentAnswerTask], int]:
        base_query = (
            select(StudentAnswerTask)
            .options(selectinload(StudentAnswerTask.task))
            .where(StudentAnswerTask.user_id == user_id)
        )
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()
        query = (
            base_query.order_by(
                StudentAnswerTask.submitted_at.desc(),
                StudentAnswerTask.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        answers = list((await self.db.execute(query)).scalars().all())
        return answers, total

    @handle_integrity_error
    async def review_answer(
        self, answer_id: int, status: StudentAnswerStatus
    ) -> StudentAnswerTask:
        answer = await self.get_answer(answer_id)
        if answer is None:
            raise NotFoundError("Answer not found")

        old_status = answer.status
        if old_status != status:
            delta = 0
            if old_status != StudentAnswerStatus.POSITIVE and status == StudentAnswerStatus.POSITIVE:
                delta = answer.task.points
            elif old_status == StudentAnswerStatus.POSITIVE and status != StudentAnswerStatus.POSITIVE:
                delta = -answer.task.points

            answer.status = status
            if delta:
                await self.db.execute(
                    update(User)
                    .where(User.id == answer.user_id)
                    .values(scores=func.greatest(0, User.scores + delta))
                )
            await self.db.commit()
            await self.db.refresh(answer)

        return answer
