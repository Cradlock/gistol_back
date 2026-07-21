from fastapi import HTTPException, status

# --- 400 Bad Request (Ошибки клиента в запросе) ---

def bad_request_exception(detail: str = "Bad request") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )

# --- 401 Unauthorized (Проблемы с токеном / авторизацией) ---

def unauthorized_exception(detail: str = "Not authenticated") -> HTTPException:
    """Используется, когда токен невалидный, просрочен или отсутствует"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

# --- 403 Forbidden (Токен ок, но нет прав доступа) ---

def forbidden_exception(detail: str = "Permission denied") -> HTTPException:
    """Используется, например, если обычный юзер пытается зайти в админку"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )

# --- 404 Not Found (Ресурс не найден) ---

def not_found_exception(detail: str = "Resource not found") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )

# --- 409 Conflict (Нарушение уникальности / бизнес-логики) ---

def conflict_exception(detail: str = "Resource already exists") -> HTTPException:
    """Используется, если, например, регистрируют уже существующий email/telegram_id"""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )

# --- 422 Unprocessable Entity (Ошибки валидации данных) ---

def validation_exception(detail: str = "Validation error") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail
    )

# --- 500 Internal Server Error (Когда что-то пошло не так у нас) ---

def internal_server_exception(detail: str = "Internal server error") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )
