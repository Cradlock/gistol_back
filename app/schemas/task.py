from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.task import StudentAnswerStatus


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
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
    group_id: int | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    points: int | None = Field(default=None, ge=1)


class TaskResponse(BaseModel):
    id: int
    title: str
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

    class Config:
        from_attributes = True


class AnswerListResponse(BaseModel):
    total: int
    answers: list[AnswerResponse]
