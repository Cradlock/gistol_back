from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.task import StudentAnswerStatus
from app.schemas.group import GroupResponse


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1, max_length=4000)
    group_ids: list[int] = Field(..., min_length=1)
    start_at: datetime
    end_at: datetime
    points: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_payload(self):
        self.group_ids = list(dict.fromkeys(self.group_ids))
        if not self.group_ids:
            raise ValueError("Нужна хотя бы одна группа")
        if self.end_at <= self.start_at:
            raise ValueError("Дата конца должна быть позже даты начала")
        return self


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    group_ids: list[int] | None = Field(default=None, min_length=1)
    start_at: datetime | None = None
    end_at: datetime | None = None
    points: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_groups(self):
        if self.group_ids is not None:
            self.group_ids = list(dict.fromkeys(self.group_ids))
            if not self.group_ids:
                raise ValueError("Нужна хотя бы одна группа")
        return self


class TaskResponse(BaseModel):
    id: int
    title: str
    content: str
    group_ids: list[int]
    groups: list[GroupResponse] = Field(default_factory=list)
    start_at: datetime
    end_at: datetime
    points: int


class TaskListResponse(BaseModel):
    total: int
    tasks: list[TaskResponse]


class AnswerReview(BaseModel):
    status: StudentAnswerStatus


class AnswerResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    text: str
    status: StudentAnswerStatus
    submitted_at: datetime
    student_name: str | None = None
    group_title: str | None = None

    class Config:
        from_attributes = True


class AnswerListResponse(BaseModel):
    total: int
    answers: list[AnswerResponse]


class AnswerSubmit(BaseModel):
    text: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_text(self):
        self.text = self.text.strip()
        if not self.text:
            raise ValueError("Ответ не может быть пустым")
        return self


class AnswerHistoryResponse(BaseModel):
    id: int
    task_id: int
    task_title: str
    task_content: str
    task_end_at: datetime
    points: int
    text: str
    status: StudentAnswerStatus
    submitted_at: datetime


class AnswerHistoryListResponse(BaseModel):
    total: int
    answers: list[AnswerHistoryResponse]
