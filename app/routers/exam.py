from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_current_student_or_higher,
    get_current_teacher,
    get_exam_service,
)
from app.models.user import User
from app.schemas.exam import (
    AnswerReview,
    AnswerSavedResponse,
    AnswerUpsert,
    ExamCreate,
    ExamListResponse,
    ExamResponse,
    ExamUpdate,
    QuestionResponse,
    QuestionUpdate,
    QuestionWrite,
    SessionListResponse,
    SessionStartResponse,
    SessionSubmitResponse,
    SessionTakeResponse,
    StudentHistoryListResponse,
    TargetResponse,
    TargetWrite,
    TeacherSessionDetail,
)
from app.services.exam import ExamService


router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("/available", response_model=ExamListResponse)
async def available_exams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_available(user, page, page_size)


@router.get("/history", response_model=StudentHistoryListResponse)
async def exam_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_history(user, page, page_size)


@router.get("/sessions/{session_id}", response_model=TeacherSessionDetail)
async def session_detail(
    session_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.get_session_detail(session_id)


@router.get("/sessions/{session_id}/take", response_model=SessionTakeResponse)
async def take_session(
    session_id: int,
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.take_session(session_id, user)


@router.put(
    "/sessions/{session_id}/answers/{question_id}",
    response_model=AnswerSavedResponse,
)
async def save_answer(
    session_id: int,
    question_id: int,
    data: AnswerUpsert,
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.save_answer(
        session_id, question_id, user, data.model_dump()
    )


@router.post(
    "/sessions/{session_id}/submit", response_model=SessionSubmitResponse
)
async def submit_session(
    session_id: int,
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.submit_session(session_id, user)


@router.patch(
    "/sessions/{session_id}/answers/{answer_id}",
    response_model=TeacherSessionDetail,
)
async def review_answer(
    session_id: int,
    answer_id: int,
    data: AnswerReview,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.review_answer(session_id, answer_id, data.accepted)


@router.get("/", response_model=ExamListResponse)
async def list_exams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=250),
    group_id: int | None = Query(default=None),
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_exams(page, page_size, search, group_id)


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    data: ExamCreate,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.create_exam(data.model_dump())


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.get_exam(exam_id)


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    data: ExamUpdate,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.update_exam(exam_id, data.model_dump(exclude_unset=True))


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    await service.delete_exam(exam_id)


@router.post(
    "/{exam_id}/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_exam(
    exam_id: int,
    user: User = Depends(get_current_student_or_higher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.start_session(exam_id, user)


@router.post(
    "/{exam_id}/targets",
    response_model=TargetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_target(
    exam_id: int,
    data: TargetWrite,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.create_target(exam_id, data.model_dump())


@router.get("/{exam_id}/targets", response_model=list[TargetResponse])
async def list_targets(
    exam_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_targets(exam_id)


@router.get("/{exam_id}/targets/{target_id}", response_model=TargetResponse)
async def get_target(
    exam_id: int,
    target_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.get_target(exam_id, target_id)


@router.patch("/{exam_id}/targets/{target_id}", response_model=TargetResponse)
async def update_target(
    exam_id: int,
    target_id: int,
    data: TargetWrite,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.update_target(exam_id, target_id, data.model_dump())


@router.delete(
    "/{exam_id}/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_target(
    exam_id: int,
    target_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    await service.delete_target(exam_id, target_id)


@router.post(
    "/{exam_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    exam_id: int,
    data: QuestionWrite,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.create_question(exam_id, data.model_dump())


@router.get("/{exam_id}/questions", response_model=list[QuestionResponse])
async def list_questions(
    exam_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_questions(exam_id)


@router.get(
    "/{exam_id}/questions/{question_id}", response_model=QuestionResponse
)
async def get_question(
    exam_id: int,
    question_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.get_question(exam_id, question_id)


@router.put("/{exam_id}/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    exam_id: int,
    question_id: int,
    data: QuestionUpdate,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.update_question(exam_id, question_id, data.model_dump())


@router.delete(
    "/{exam_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_question(
    exam_id: int,
    question_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    await service.delete_question(exam_id, question_id)


@router.get("/{exam_id}/sessions", response_model=SessionListResponse)
async def list_sessions(
    exam_id: int,
    _teacher: User = Depends(get_current_teacher),
    service: ExamService = Depends(get_exam_service),
):
    return await service.list_sessions(exam_id)
