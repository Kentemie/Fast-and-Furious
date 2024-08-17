import warnings

from typing import Self, Annotated, Optional

from pydantic import (
    AnyUrl,
    BeforeValidator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.utils import parse_cors

from .db import Database
from .redis import Redis
from .api import Api
from .auth import Authentication


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_ignore_empty=True,
        extra="ignore",
        env_nested_delimiter="__",
    )

    DOMAIN: Optional[str] = None

    ENVIRONMENT: str

    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []
    SECRET_KEY: str

    DATABASE: Database

    REDIS: Redis

    API: Api = Api()

    AUTH: Authentication = Authentication()

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("DATABASE__PASSWORD", self.DATABASE.PASSWORD)

        return self

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "change_this":
            message = (
                f'The value of {var_name} is "change_this", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


settings = Settings()
