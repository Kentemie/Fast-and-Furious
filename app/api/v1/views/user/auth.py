from typing import TYPE_CHECKING, Annotated, Optional

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

    get_current_active_user_access_token = authenticator.get_current_user_token(
        required_token_type=settings.AUTH.ACCESS_TOKEN,
        verified=requires_verification,
    )
    get_current_user_refresh_token = authenticator.get_current_user_token(
        required_token_type=settings.AUTH.REFRESH_TOKEN,
        optional=True,
        verified=requires_verification,
    )
    get_current_active_user_refresh_token = authenticator.get_current_user_token(
        required_token_type=settings.AUTH.REFRESH_TOKEN,
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

    refresh_responses: "OpenAPIResponseType" = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "The refresh token is missed."
            },
            status.HTTP_403_FORBIDDEN: {"description": "The user is not verified."},
        },
        **auth_backend.transport.get_openapi_login_responses_success(),
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
        access_token: Annotated[
            tuple["User", tuple[str, int]],
            Depends(get_current_active_user_access_token),
        ],
        refresh_token: Annotated[
            tuple[Optional["User"], tuple[Optional[str], Optional[int]]],
            Depends(get_current_user_refresh_token),
        ],
    ):
        user = access_token[0]
        access_token_info = access_token[1]
        refresh_token_info = refresh_token[1]

        return await auth_backend.logout(
            user_id=user.id,
            access_token_info=access_token_info,
            refresh_token_info=refresh_token_info,
        )

    @router.post(
        "/refresh",
        name=f"auth:{auth_backend.name}.refresh",
        responses=refresh_responses,
    )
    async def refresh(
        refresh_token: Annotated[
            tuple["User", tuple[str, int]],
            Depends(get_current_active_user_refresh_token),
        ],
    ):
        user, _ = refresh_token

        return await auth_backend.login(user, is_refresh=True)

    return router
