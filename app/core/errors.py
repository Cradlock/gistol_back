from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DataError(Exception):
    status_code = 500
    default_message = "Ошибка базы данных"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(DataError):
    status_code = 404
    default_message = "Ресурс не найден"


class DuplicateError(DataError):
    status_code = 409
    default_message = "Запись с такими данными уже существует"


async def data_error_handler(_request: Request, exc: DataError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DataError, data_error_handler)
    app.add_exception_handler(NotFoundError, data_error_handler)
    app.add_exception_handler(DuplicateError, data_error_handler)
