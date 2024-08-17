from typing import TYPE_CHECKING, Literal, Optional

from fastapi import status, Response, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from app.core.schemas import BearerTokenSchema
from app.core.config import settings

if TYPE_CHECKING:
    from app.core.types import OpenAPIResponseType


class BearerTransport:
    """
    A class to handle authentication processes using Bearer tokens.

    This class manages user login, sets the refresh token cookie,
    and provides schemas for OpenAPI documentation.
    """

    def __init__(self):
        self.rt_cookie_name = settings.AUTH.REFRESH_TOKEN
        self.rt_cookie_max_age = settings.AUTH.JWT.REFRESH_TOKEN_LIFETIME_SECONDS
        self.rt_cookie_path = "/"
        self.rt_cookie_domain = settings.DOMAIN
        self.rt_cookie_secure = False if settings.ENVIRONMENT == "local" else True
        self.rt_cookie_httponly = True
        self.rt_cookie_samesite: Literal["lax", "strict", "none"] = "lax"  # noqa

        self.scheme = OAuth2PasswordBearer(
            tokenUrl=settings.API.BEARER_TOKEN_URL, auto_error=False
        )

    async def get_login_response(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
    ) -> Response:
        """
        Generate a response for the login or token refresh operation.

        If a refresh token is provided, it will be set as an HTTP-only cookie.

        :param access_token: The access token to include in the response.
        :param refresh_token: The optional refresh token to be set as a cookie.
        :return: A JSON response containing the access token, and optionally setting the refresh token as a cookie.
        """

        bearer_token = BearerTokenSchema(access_token=access_token, token_type="bearer")
        response = JSONResponse(
            content=bearer_token.model_dump(), status_code=status.HTTP_200_OK
        )

        if refresh_token:
            response = self._set_login_cookie(response, refresh_token)

        return response

    async def get_logout_response(self) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)

        return self._set_logout_cookie(response)

    def _set_login_cookie(self, response: Response, refresh_token: str) -> Response:
        """
        Set the refresh token as an HTTP-only cookie in the response.

        :param response: The response object to modify.
        :param refresh_token: The refresh token to set as a cookie.
        :return: The modified response with the cookie set.
        """

        response.set_cookie(
            key=self.rt_cookie_name,
            value=refresh_token,
            max_age=self.rt_cookie_max_age,
            path=self.rt_cookie_path,
            domain=self.rt_cookie_domain,
            secure=self.rt_cookie_secure,
            httponly=self.rt_cookie_httponly,
            samesite=self.rt_cookie_samesite,
        )

        return response

    def _set_logout_cookie(self, response: Response) -> Response:
        """
        Remove the refresh token from an HTTP-only cookie in the response.

        :param response: The response object to modify.
        :return: The modified response with the cookie set.
        """

        response.set_cookie(
            key=self.rt_cookie_name,
            value="",
            max_age=0,
            path=self.rt_cookie_path,
            domain=self.rt_cookie_domain,
            secure=self.rt_cookie_secure,
            httponly=self.rt_cookie_httponly,
            samesite=self.rt_cookie_samesite,
        )

        return response

    async def get_cookie(self, request: Request) -> Optional[str]:
        return request.cookies.get(self.rt_cookie_name)

    @staticmethod
    def get_openapi_login_responses_success() -> "OpenAPIResponseType":
        """
        Provide OpenAPI schema for a successful login response.

        :return: A dictionary representing the OpenAPI schema for a successful login response.
        """

        return {
            status.HTTP_200_OK: {
                "model": BearerTokenSchema,
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1"
                            "c2VyX2lkIjoiOTIyMWZmYzktNjQwZi00MzcyLTg2Z"
                            "DMtY2U2NDJjYmE1NjAzIiwiYXVkIjoiZmFzdGFwaS"
                            "11c2VyczphdXRoIiwiZXhwIjoxNTcxNTA0MTkzfQ."
                            "M10bjOe45I5Ncu_uXvOmVV8QxnL-nZfcH96U90JaocI",
                            "token_type": "bearer",
                        }
                    }
                },
            },
        }

    @staticmethod
    def get_openapi_logout_responses_success() -> "OpenAPIResponseType":
        """
        Provide OpenAPI schema for a successful logout response.

        :return: A dictionary representing the OpenAPI schema for a successful logout response.
        """
        return {status.HTTP_204_NO_CONTENT: {"model": None}}
