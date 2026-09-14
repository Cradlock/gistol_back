from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_teacher, get_task_service
from app.models.user import User
from app.schemas.task import (
    AnswerListResponse,
    AnswerResponse,
    AnswerReview,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.task import TaskService

router = APIRouter(
    prefix="/task",
    tags=["Tasks"],
)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    group_id: int | None = Query(default=None, description="Фильтр по группе"),
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.list_tasks(group_id)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.create_task(data.model_dump())


@router.patch("/answers/{answer_id}", response_model=AnswerResponse)
async def review_answer(
    answer_id: int,
    data: AnswerReview,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.review_answer(answer_id, data.status)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.update_task(task_id, data.model_dump(exclude_unset=True))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    await service.delete_task(task_id)


@router.get("/{task_id}/answers", response_model=AnswerListResponse)
async def list_task_answers(
    task_id: int,
    admin: User = Depends(get_current_teacher),
    service: TaskService = Depends(get_task_service),
):
    return await service.list_answers(task_id)
