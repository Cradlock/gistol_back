from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.exam import ExamSessionStatus, QuestionType
from app.models.years import Year


class ChoiceWrite(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    is_correct: bool = False


class ChoiceResponse(ChoiceWrite):
    id: int
    model_config = {"from_attributes": True}


class StudentChoiceResponse(BaseModel):
    id: int
    text: str
    model_config = {"from_attributes": True}


class QuestionWrite(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    type: QuestionType
    points: int = Field(default=1, ge=1)
    position: int = Field(default=0, ge=0)
    choices: list[ChoiceWrite] = Field(default_factory=list)
    expected_answer: str | None = Field(default=None, min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_answer_shape(self):
        if self.type == QuestionType.CHOISE:
            if len(self.choices) < 2 or sum(c.is_correct for c in self.choices) != 1:
                raise ValueError("Choice question requires at least two choices and exactly one correct")
            if self.expected_answer is not None:
                raise ValueError("Choice question cannot have expected_answer")
        else:
            if self.choices or self.expected_answer is None:
                raise ValueError("Input question requires exactly one expected_answer and no choices")
        return self


class QuestionUpdate(QuestionWrite):
    pass


class QuestionResponse(BaseModel):
    id: int
    text: str
    type: QuestionType
    points: int
    position: int
    choices: list[ChoiceResponse]
    expected_answer: str | None = None


class StudentQuestionResponse(BaseModel):
    id: int
    text: str
    type: QuestionType
    points: int
    position: int
    choices: list[StudentChoiceResponse] = Field(default_factory=list)


class TargetWrite(BaseModel):
    group_id: int | None = None
    year: Year


class TargetResponse(TargetWrite):
    id: int
    model_config = {"from_attributes": True}


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    theme: str = Field(min_length=1, max_length=500)
    start_at: datetime
    duration_minutes: int = Field(ge=1)


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    theme: str | None = Field(default=None, min_length=1, max_length=500)
    start_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1)


class ExamResponse(BaseModel):
    id: int
    title: str
    theme: str
    start_at: datetime
    duration_minutes: int
    targets: list[TargetResponse] = Field(default_factory=list)
    questions: list[QuestionResponse] = Field(default_factory=list)


class ExamSummary(BaseModel):
    id: int
    title: str
    theme: str
    start_at: datetime
    duration_minutes: int
    deadline: datetime


class ExamListResponse(BaseModel):
    total: int
    exams: list[ExamSummary]


class SessionSummary(BaseModel):
    id: int
    user_id: int
    student_name: str | None
    status: ExamSessionStatus
    started_at: datetime
    submitted_at: datetime | None
    reviewed_at: datetime | None
    score: int | None


class SessionListResponse(BaseModel):
    total: int
    sessions: list[SessionSummary]


class SessionStartResponse(BaseModel):
    id: int
    exam_id: int
    status: ExamSessionStatus
    started_at: datetime
    deadline: datetime


class SessionTakeResponse(SessionStartResponse):
    title: str
    theme: str
    questions: list[StudentQuestionResponse]


class SessionSubmitResponse(BaseModel):
    id: int
    exam_id: int
    status: ExamSessionStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    score: int | None


class AnswerUpsert(BaseModel):
    choice_id: int | None = None
    text: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def exactly_one_value(self):
        if (self.choice_id is None) == (self.text is None):
            raise ValueError("Exactly one of choice_id or text is required")
        if self.text is not None:
            self.text = self.text.strip()
            if not self.text:
                raise ValueError("Text answer cannot be blank")
        return self


class AnswerSavedResponse(BaseModel):
    id: int
    session_id: int
    question_id: int
    choice_id: int | None
    text: str | None
    model_config = {"from_attributes": True}


class AnswerReview(BaseModel):
    accepted: bool


class TeacherAnswerResponse(BaseModel):
    id: int
    question_id: int
    question_text: str
    question_type: QuestionType
    question_points: int
    choice_id: int | None
    choice_text: str | None
    text: str | None
    awarded_points: int | None
    reviewed_at: datetime | None
    choices: list[ChoiceResponse] = Field(default_factory=list)


class TeacherSessionDetail(BaseModel):
    id: int
    user_id: int
    student_name: str | None
    exam_id: int
    exam_title: str
    exam_theme: str
    status: ExamSessionStatus
    started_at: datetime
    submitted_at: datetime | None
    reviewed_at: datetime | None
    score: int | None
    answers: list[TeacherAnswerResponse]
