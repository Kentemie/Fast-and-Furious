from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from pydantic import EmailStr

from app.core.exceptions import (
    UserAlreadyVerified,
    UserInactive,
    UserNotExists,
    ErrorModel,
    ErrorCode,
    InvalidVerificationCode,
)
from app.core.config import settings
from app.core.schemas import UserSchema

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager, UserManagerDependency

    from app.core.types import OpenAPIResponseType


def get_verify_router(get_user_manager: "UserManagerDependency"):
    """Generate a router with the user verification routes."""

    router = APIRouter(
        prefix=settings.API.V1.RESET_PASSWORD_EP,
        tags=["Verification"],
    )

    verify_responses: "OpenAPIResponseType" = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.VERIFY_USER_BAD_CODE: {
                            "summary": "Bad code, not existing user or"
                            "not the e-mail currently set for the user.",
                            "value": {"detail": ErrorCode.VERIFY_USER_BAD_CODE},
                        },
                        ErrorCode.VERIFY_USER_ALREADY_VERIFIED: {
                            "summary": "The user is already verified.",
                            "value": {"detail": ErrorCode.VERIFY_USER_ALREADY_VERIFIED},
                        },
                    }
                }
            },
        }
    }

    @router.post(
        "/request-verify-code",
        status_code=status.HTTP_202_ACCEPTED,
        name="verify:request-code",
    )
    async def request_verify_token(
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
        email: EmailStr = Body(..., embed=True),
    ):
        try:
            user = await user_manager.get_by_email(email)
            await user_manager.request_verify(user)
        except (
            UserNotExists,
            UserInactive,
            UserAlreadyVerified,
        ):
            pass

        return None

    @router.post(
        "/verify",
        response_model=UserSchema,
        name="verify:verify",
        responses=verify_responses,
    )
    async def verify(
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
        code: str = Body(..., embed=True),
    ):
        try:
            user = await user_manager.verify(code)
            return UserSchema.model_validate(user)
        except (InvalidVerificationCode, UserNotExists):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_BAD_CODE,
            )
        except UserAlreadyVerified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.VERIFY_USER_ALREADY_VERIFIED,
            )

    return router
