from .base import Base

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    email: Mapped[str] = mapped_column(
        String(length=320),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(length=64),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(length=64),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
