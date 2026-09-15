from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.task import StudentAnswerStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1, max_length=4000)
    group_id: int
    start_at: datetime
    end_at: datetime
    points: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_at <= self.start_at:
            raise ValueError("Дата конца должна быть позже даты начала")
        return self


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    group_id: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    points: int | None = Field(default=None, ge=1)


class TaskResponse(BaseModel):
    id: int
    title: str
    content: str
    group_id: int
    start_at: datetime
    end_at: datetime
    points: int

    class Config:
        from_attributes = True


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
