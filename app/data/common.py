from functools import wraps

from sqlalchemy.exc import IntegrityError

from app.core.errors import DuplicateError


def handle_integrity_error(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except IntegrityError:
            await self.db.rollback()
            raise DuplicateError()

    return wrapper
