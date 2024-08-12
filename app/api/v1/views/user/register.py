from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import (
    ErrorModel,
    ErrorCode,
    InvalidPasswordException,
    UserAlreadyExists,
)
from app.core.config import settings
from app.core.schemas import UserSchema, UserCreateSchema

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager, UserManagerDependency

    from app.core.types import OpenAPIResponseType


def get_register_router(get_user_manager: "UserManagerDependency") -> APIRouter:
    """Generate a router with the register route."""

    router = APIRouter(
        prefix=settings.API.V1.REGISTER_EP,
        tags=["Register"],
    )

    register_responses: "OpenAPIResponseType" = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.REGISTER_USER_ALREADY_EXISTS: {
                            "summary": "A user with this email already exists.",
                            "value": {"detail": ErrorCode.REGISTER_USER_ALREADY_EXISTS},
                        },
                        ErrorCode.REGISTER_INVALID_PASSWORD: {
                            "summary": "Password validation failed.",
                            "value": {
                                "detail": {
                                    "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                                    "reason": "Password should be"
                                    "at least 3 characters",
                                }
                            },
                        },
                    }
                }
            },
        },
    }

    @router.post(
        "/register",
        response_model=UserSchema,
        status_code=status.HTTP_201_CREATED,
        name="register:register",
        responses=register_responses,
    )
    async def register(
        user_create: UserCreateSchema,
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ):
        try:
            created_user = await user_manager.create(user_create, safe=True)
        except UserAlreadyExists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
            )
        except InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                    "reason": e.reason,
                },
            )

        return UserSchema.model_validate(created_user)

    return router
