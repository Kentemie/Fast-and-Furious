from typing import TYPE_CHECKING, Literal

from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import TransportLogoutNotSupportedError
from app.core.schemas import BearerTokenSchema
from app.core.config import settings

if TYPE_CHECKING:
    from fastapi import Response

    from app.core.types import OpenAPIResponseType


class BearerTransport:
    def __init__(self):
        self.rt_cookie_name = settings.AUTH.REFRESH_TOKEN
        self.rt_cookie_max_age = settings.AUTH.JWT.REFRESH_TOKEN_LIFETIME_SECONDS
        self.rt_cookie_path = "/"
        self.rt_cookie_domain = settings.DOMAIN
        self.rt_cookie_secure = False if settings.ENVIRONMENT == "local" else True
        self.rt_cookie_httponly = True
        self.rt_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

        self.scheme = OAuth2PasswordBearer(
            tokenUrl=settings.API.BEARER_TOKEN_URL, auto_error=False
        )

    async def get_login_response(
        self,
        access_token: str,
        refresh_token: str,
    ) -> "Response":
        bearer_token = BearerTokenSchema(access_token=access_token, token_type="bearer")
        response = JSONResponse(
            content=bearer_token.model_dump(), status_code=status.HTTP_200_OK
        )

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

    async def get_logout_response(self) -> "Response":
        raise TransportLogoutNotSupportedError()

    @staticmethod
    def get_openapi_login_responses_success() -> "OpenAPIResponseType":
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
        return {}
