from typing import Any, Optional

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data.common import handle_integrity_error
from app.models.user import User


class AuthDataSQLAlchemy:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.group))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_field(self, field: str, value: Any) -> Optional[User]:
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")

        query = (
            select(User)
            .where(column == value)
            .options(selectinload(User.group))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_field(self, field: str, value: Any) -> list[User]:
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")

        query = (
            select(User)
            .where(column == value)
            .options(selectinload(User.group))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    @handle_integrity_error
    async def create_user(self, user_data: dict[str, Any]) -> User:
        new_user = User(**user_data)
        self.db.add(new_user)
        await self.db.flush()
        user_id = new_user.id
        await self.db.commit()
        loaded = await self.get_by_id(user_id)
        if loaded is None:
            raise RuntimeError("Failed to reload created user")
        return loaded

    @handle_integrity_error
    async def update_user(self, user_id: int, update_data: dict[str, Any]) -> Optional[User]:
        query = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def exists_by_field(self, val_id: int, field: str = "telegram_id") -> bool:
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")

        query = select(exists().where(column == val_id))
        result = await self.db.execute(query)
        return bool(result.scalar())
