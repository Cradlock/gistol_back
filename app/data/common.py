from functools import wraps

from sqlalchemy.exc import IntegrityError

from app.core.errors import DuplicateError


def handle_integrity_error(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except IntegrityError as exc:
            await self.db.rollback()
            orig = getattr(exc, "orig", None)
            sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
            orig_name = type(orig).__name__ if orig is not None else ""
            if (
                sqlstate == "23505"
                or "UniqueViolation" in orig_name
                or "unique constraint" in str(exc).lower()
            ):
                raise DuplicateError() from exc
            raise

    return wrapper
