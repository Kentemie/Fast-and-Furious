from typing import TYPE_CHECKING, Optional

from app.api.v1.authentication.jwt_bearer import JWTStrategy, BearerTransport

from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import Response

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

    async def login(self, user: "User", is_refresh: bool = False) -> "Response":
        """
        Handle user login or token refresh.

        :param user: The user object for whom the tokens will be generated.
        :param is_refresh: A flag indicating whether this is a token refresh operation.
        :return: A response containing the access token, and optionally the refresh token.
        """
        access_token = await self.strategy.write_token(
            user=user, token_type=settings.AUTH.ACCESS_TOKEN
        )

        if is_refresh:
            return await self.transport.get_login_response(access_token)
        else:
            refresh_token = await self.strategy.write_token(
                user=user, token_type=settings.AUTH.REFRESH_TOKEN
            )
            return await self.transport.get_login_response(access_token, refresh_token)

    async def logout(
        self,
        user_id: int,
        access_token_info: tuple[str, int],
        refresh_token_info: tuple[Optional[str], Optional[int]],
    ) -> "Response":
        """
        Handle user logout and token invalidation.

        :param user_id: The user id for whom the tokens will be invalidated.
        :param access_token_info: The access token information (token itself and
        its expiration time).
        :param refresh_token_info: The refresh token information (token itself and
        its expiration time).
        :return: A response indicating the result of the logout operation.
        """
        await self.strategy.destroy_token(
            user_id, access_token_info, refresh_token_info
        )

        response = await self.transport.get_logout_response()

        return response


auth_backend = AuthenticationBackend()
