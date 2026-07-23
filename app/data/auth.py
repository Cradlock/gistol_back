
from typing import Any, Optional
from sqlalchemy import select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing_extensions import override

# Импортируем абстрактный класс и модель
from app.services.auth import AuthDataAbstract
from app.models.user import User


class AuthDataSQLAlchemy(AuthDataAbstract):
    def __init__(self, db: AsyncSession):
        self.db = db     

    @override
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получение пользователя по первичному ключу.
        Автоматически подгружаем связанные объекты group,
        чтобы к ним можно было безопасно обращаться в асинхронном режиме.
        """
        query = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.group)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @override
    async def get_by_field(self, field: str, value: Any) -> Optional[User]:
        """
        Универсальный поиск по любому полю модели User.
        Например: field="telegram_id", value=6290788263 или field="email", value="test@test.com"
        """
        # Динамически получаем атрибут колонки из класса User
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")
             
        query = (
            select(User)
            .where(column == value)
            .options(
                selectinload(User.group)
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    @override
    async def get_all_by_field(self, field: str, value: Any) -> list[User]:
        """Универсальный метод получения СПИСКА пользователей по полю (например, group_id)"""
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")
             
        query = (
            select(User)
            .where(column == value)
            .options(
                selectinload(User.group)
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()) 

    @override
    async def create_user(self, user_data: dict[str, Any]) -> User:
        """
        Создание нового пользователя. 
        На входе принимает словарь с данными (например, из Pydantic схемы).
        """
        new_user = User(**user_data)
        self.db.add(new_user)
        # Коммитим транзакцию в БД
        await self.db.commit()
        # Обновляем объект, чтобы подтянулись дефолтные значения из БД (id, created_at)
        await self.db.refresh(new_user)
        return new_user

    @override
    async def update_user(self, user_id: int, update_data: dict[str, Any]) -> Optional[User]:
        """
        Обновление полей пользователя по его ID.
        """
        query = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()

    @override
    async def exists_by_field(self, val_id: int,field: str = "telegram_id") -> bool:
        """
        Быстрая проверка существования пользователя по val_id без загрузки всей сущности.
        """
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"Модель User не имеет поля '{field}'")
         

        query = select(exists().where(column == val_id))

        result = await self.db.execute(query)
        
        return bool(result.scalar())



