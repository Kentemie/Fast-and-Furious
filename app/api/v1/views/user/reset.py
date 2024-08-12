from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from pydantic import EmailStr

from app.core.exceptions import (
    ErrorModel,
    ErrorCode,
    UserNotExists,
    UserInactive,
    InvalidResetPasswordToken,
    InvalidPasswordException,
)
from app.core.config import settings

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager, UserManagerDependency

    from app.core.types import OpenAPIResponseType


def get_reset_password_router(get_user_manager: "UserManagerDependency") -> APIRouter:
    """Generate a router with the reset password routes."""

    router = APIRouter(
        prefix=settings.API.V1.RESET_PASSWORD_EP,
        tags=["Reset password"],
    )

    reset_password_responses: "OpenAPIResponseType" = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.RESET_PASSWORD_BAD_TOKEN: {
                            "summary": "Bad or expired token.",
                            "value": {"detail": ErrorCode.RESET_PASSWORD_BAD_TOKEN},
                        },
                        ErrorCode.RESET_PASSWORD_INVALID_PASSWORD: {
                            "summary": "Password validation failed.",
                            "value": {
                                "detail": {
                                    "code": ErrorCode.RESET_PASSWORD_INVALID_PASSWORD,
                                    "reason": "Password should be at least 3 characters",
                                }
                            },
                        },
                    }
                }
            },
        },
    }

    @router.post(
        "/forgot-password",
        status_code=status.HTTP_202_ACCEPTED,
        name="reset:forgot_password",
    )
    async def forgot_password(
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
        email: EmailStr = Body(..., embed=True),
    ):
        try:
            user = await user_manager.get_by_email(email)
        except UserNotExists:
            return None

        try:
            await user_manager.forgot_password(user)
        except UserInactive:
            pass

        return None

    @router.post(
        "/reset-password",
        name="reset:reset_password",
        responses=reset_password_responses,
    )
    async def reset_password(
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
        token: str = Body(...),
        password: str = Body(...),
    ):
        try:
            await user_manager.reset_password(token, password)
        except (
            InvalidResetPasswordToken,
            UserNotExists,
            UserInactive,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.RESET_PASSWORD_BAD_TOKEN,
            )
        except InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.RESET_PASSWORD_INVALID_PASSWORD,
                    "reason": e.reason,
                },
            )

    return router
