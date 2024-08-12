from typing import TYPE_CHECKING

from fastapi import status, Response

from app.api.v1.authentication.jwt_bearer import JWTStrategy, BearerTransport

from app.core.exceptions import (
    JWTStrategyDestroyNotSupportedError,
    TransportLogoutNotSupportedError,
)
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.models import User


class AuthenticationBackend:
    """
    Combination of an authentication transport and strategy.

    Together, they provide a full authentication method logic.
    """

    def __init__(self):
        self.name = settings.AUTH.JWT.BACKEND_NAME
        self.transport = BearerTransport()
        self.strategy = JWTStrategy()

    async def login(self, user: "User") -> Response:
        access_token = await self.strategy.write_token(
            user=user, token_type=settings.AUTH.ACCESS_TOKEN
        )
        refresh_token = await self.strategy.write_token(
            user=user, token_type=settings.AUTH.REFRESH_TOKEN
        )

        return await self.transport.get_login_response(access_token, refresh_token)

    async def logout(self, token: str) -> Response:
        try:
            await self.strategy.destroy_token(token)
        except JWTStrategyDestroyNotSupportedError:
            pass

        try:
            response = await self.transport.get_logout_response()
        except TransportLogoutNotSupportedError:
            response = Response(status_code=status.HTTP_204_NO_CONTENT)

        return response


auth_backend = AuthenticationBackend()
