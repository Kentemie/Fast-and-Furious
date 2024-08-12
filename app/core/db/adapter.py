from typing import Any, AsyncGenerator, TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from app.core.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
    )


class DatabaseAdapter:
    def __init__(
        self,
        database_url: str,
        kwargs: Any = None,
    ) -> None:
        self.async_engine: "AsyncEngine" = create_async_engine(
            url=database_url,
            **kwargs,
        )
        self.async_session_factory: async_sessionmaker["AsyncSession"] = (
            async_sessionmaker(
                bind=self.async_engine,
                autoflush=False,
                autocommit=False,
                expire_on_commit=False,
            )
        )

    async def dispose(self) -> None:
        await self.async_engine.dispose()

    async def get_async_session(self) -> AsyncGenerator["AsyncSession", None]:
        async with self.async_session_factory() as session:
            yield session


adapter = DatabaseAdapter(
    database_url=settings.DATABASE.SQLALCHEMY_DATABASE_URI,
    kwargs={
        "echo": True if settings.ENVIRONMENT != "local" else False,
    },
)
