import jwt

from typing import Optional, TYPE_CHECKING

from app.api.v1.utils import decode_jwt, generate_jwt

from app.core.config import settings
from app.core.exceptions import (
    JWTStrategyDestroyNotSupportedError,
    UserNotExists,
    InvalidID,
)

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager

    from app.core.models import User


class JWTStrategy:
    def __init__(self):
        self.private_key: str = settings.AUTH.JWT.PRIVATE_KEY.read_text()
        self.public_key: str = settings.AUTH.JWT.PUBLIC_KEY.read_text()
        self.lifetime_seconds: dict[str, int] = {
            settings.AUTH.ACCESS_TOKEN: settings.AUTH.JWT.ACCESS_TOKEN_LIFETIME_SECONDS,
            settings.AUTH.REFRESH_TOKEN: settings.AUTH.JWT.REFRESH_TOKEN_LIFETIME_SECONDS,
        }
        self.token_audience: str = settings.AUTH.JWT.TOKEN_AUDIENCE
        self.algorithm: str = settings.AUTH.JWT.ALGORITHM

    async def read_token(
        self, token: str, user_manager: "UserManager", required_token_type: str
    ) -> Optional["User"]:
        try:
            data = decode_jwt(
                encoded_jwt=token,
                public_key=self.public_key,
                audience=self.token_audience,
                algorithms=[self.algorithm],
            )

            user_id = data.get("sub")
            token_type = data.get(settings.AUTH.TOKEN_TYPE)

            if user_id is None or token_type is None:
                return None
            if token_type != required_token_type:
                return None
        except jwt.PyJWTError:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (UserNotExists, InvalidID):
            return None

    async def write_token(self, user: "User", token_type: str) -> str:
        data = {
            "sub": str(user.id),
            settings.AUTH.TOKEN_TYPE: token_type,
        }

        return generate_jwt(
            data=data,
            private_key=self.private_key,
            audience=self.token_audience,
            lifetime_seconds=self.lifetime_seconds[token_type],
            algorithm=self.algorithm,
        )

    async def destroy_token(self, token: str) -> None:
        raise JWTStrategyDestroyNotSupportedError()
