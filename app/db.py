from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

SQLALCHEMY_DATABASE_URL = settings.db_url.replace("postgresql://", "postgresql+asyncpg://")


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.debug,      # каждый запрос виден в терминале 
    pool_size=10,   # количество открытых соединений с бд
    max_overflow=20 # количество дополнительных соединений с бд (на крайний случай)
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,        # Указание чтобы sessionmaker использовать ассинхроность
    expire_on_commit=False      # Отключает тайные синхронные коммиты в бд
)








