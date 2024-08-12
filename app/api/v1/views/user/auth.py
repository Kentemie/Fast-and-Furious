from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.authentication.backend import auth_backend

from app.core.config import settings
from app.core.exceptions import ErrorModel, ErrorCode

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager, UserManagerDependency
    from app.api.v1.authentication.authenticator import Authenticator

    from app.core.models import User
    from app.core.types import OpenAPIResponseType


def get_auth_router(
    get_user_manager: "UserManagerDependency",
    authenticator: "Authenticator",
    requires_verification: bool = True,
) -> APIRouter:
    """Generate a router with login/logout routes for an authentication backend."""

    router = APIRouter(
        prefix=settings.API.V1.AUTH_EP,
        tags=["Auth"],
    )

    get_current_user_token = authenticator.get_current_user_token(
        verified=requires_verification,
    )

    login_responses: "OpenAPIResponseType" = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "Bad credentials or the user is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value": {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                    }
                }
            },
        },
        **auth_backend.transport.get_openapi_login_responses_success(),
    }

    logout_responses: "OpenAPIResponseType" = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user."
            }
        },
        **auth_backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{auth_backend.name}.login",
        responses=login_responses,
    )
    async def login(
        credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ):
        user = await user_manager.authenticate(credentials)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        response = await auth_backend.login(user)

        return response

    @router.post(
        "/logout",
        name=f"auth:{auth_backend.name}.logout",
        responses=logout_responses,
    )
    async def logout(
        user_token: Annotated[tuple["User", str], Depends(get_current_user_token)],
    ):
        _, token = user_token
        return await auth_backend.logout(token)

    return router
