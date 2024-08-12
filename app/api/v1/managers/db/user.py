from typing import TYPE_CHECKING, Optional, Any

from fastapi import Depends

from sqlalchemy import select, func

from app.core.models import User
from app.core.db import adapter

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


class UserDatabaseManager:
    """
    :param session: SQLAlchemy session instance.
    """

    def __init__(self, session: "AsyncSession"):
        self.session = session

    async def get(self, user_id: int) -> Optional[User]:
        statement = select(User).where(User.id == user_id)
        return await self._get_user(statement)

    async def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(
            func.lower(User.email) == func.lower(email)  # type: ignore
        )
        return await self._get_user(statement)

    async def create(self, create_dict: dict[str, Any]) -> User:
        user = User(**create_dict)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, update_dict: dict[str, Any]) -> User:
        for key, value in update_dict.items():
            setattr(user, key, value)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()

    async def _get_user(self, statement: "Select") -> Optional[User]:
        results = await self.session.execute(statement)
        return results.unique().scalar_one_or_none()


async def get_user_db_manager(
    session: "AsyncSession" = Depends(adapter.get_async_session),
):
    yield UserDatabaseManager(session=session)
