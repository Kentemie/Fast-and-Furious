from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.exceptions import (
    UserNotExists,
    InvalidID,
    ErrorModel,
    ErrorCode,
    InvalidPasswordException,
    UserAlreadyExists,
)
from app.core.config import settings
from app.core.schemas import UserSchema, UserUpdateSchema

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager, UserManagerDependency
    from app.api.v1.authentication.authenticator import Authenticator

    from app.core.types import OpenAPIResponseType
    from app.core.models import User


def get_users_router(
    get_user_manager: "UserManagerDependency",
    authenticator: "Authenticator",
    requires_verification: bool = True,
) -> APIRouter:
    """Generate a router with the authentication routes."""

    router = APIRouter(
        prefix=settings.API.V1.USERS_EP,
        tags=["Users"],
    )

    me_responses: "OpenAPIResponseType" = {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
    }

    update_me_responses: "OpenAPIResponseType" = {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS: {
                            "summary": "A user with this email already exists.",
                            "value": {
                                "detail": ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS
                            },
                        },
                        ErrorCode.UPDATE_USER_INVALID_PASSWORD: {
                            "summary": "Password validation failed.",
                            "value": {
                                "detail": {
                                    "code": ErrorCode.UPDATE_USER_INVALID_PASSWORD,
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

    get_user_responses: "OpenAPIResponseType" = {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not a superuser.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The user does not exist.",
        },
    }

    update_user_responses: "OpenAPIResponseType" = {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not a superuser.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The user does not exist.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS: {
                            "summary": "A user with this email already exists.",
                            "value": {
                                "detail": ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS
                            },
                        },
                        ErrorCode.UPDATE_USER_INVALID_PASSWORD: {
                            "summary": "Password validation failed.",
                            "value": {
                                "detail": {
                                    "code": ErrorCode.UPDATE_USER_INVALID_PASSWORD,
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

    delete_user_responses: "OpenAPIResponseType" = {
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Missing token or inactive user.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Not a superuser.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The user does not exist.",
        },
    }

    get_current_user = authenticator.get_current_user(
        verified=requires_verification,
    )
    get_current_superuser = authenticator.get_current_user(
        verified=requires_verification,
        superuser=True,
    )

    async def get_user_or_404(
        user_id: str,
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ) -> "User":
        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (UserNotExists, InvalidID) as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e

    @router.get(
        "/me",
        response_model=UserSchema,
        name="users:current_user",
        responses=me_responses,
    )
    async def me(
        user: Annotated["User", Depends(get_current_user)],
    ):
        return UserSchema.model_validate(user)

    @router.patch(
        "/me",
        response_model=UserSchema,
        dependencies=[Depends(get_current_user)],
        name="users:patch_current_user",
        responses=update_me_responses,
    )
    async def update_me(
        user_update: UserUpdateSchema,
        user: Annotated["User", Depends(get_current_user)],
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ):
        try:
            user = await user_manager.update(user_update, user, safe=True)
            return UserSchema.model_validate(user)
        except InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.UPDATE_USER_INVALID_PASSWORD,
                    "reason": e.reason,
                },
            )
        except UserAlreadyExists:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS,
            )

    @router.get(
        "/{user_id}",
        response_model=UserSchema,
        dependencies=[Depends(get_current_superuser)],
        name="users:user",
        responses=get_user_responses,
    )
    async def get_user(
        user: Annotated["User", Depends(get_user_or_404)],
    ):
        return UserSchema.model_validate(user)

    @router.patch(
        "/{user_id}",
        response_model=UserSchema,
        dependencies=[Depends(get_current_superuser)],
        name="users:patch_user",
        responses=update_user_responses,
    )
    async def update_user(
        user_update: UserUpdateSchema,
        user: Annotated["User", Depends(get_user_or_404)],
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ):
        try:
            user = await user_manager.update(user_update, user, safe=False)
            return UserSchema.model_validate(user)
        except InvalidPasswordException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": ErrorCode.UPDATE_USER_INVALID_PASSWORD,
                    "reason": e.reason,
                },
            )
        except UserAlreadyExists:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.UPDATE_USER_EMAIL_ALREADY_EXISTS,
            )

    @router.delete(
        "/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        dependencies=[Depends(get_current_superuser)],
        name="users:delete_user",
        responses=delete_user_responses,
    )
    async def delete_user(
        user: Annotated["User", Depends(get_user_or_404)],
        user_manager: Annotated["UserManager", Depends(get_user_manager)],
    ):
        await user_manager.delete(user)
        return None

    return router
