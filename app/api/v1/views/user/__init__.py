from typing import TYPE_CHECKING

from .register import get_register_router
from .verify import get_verify_router
from .reset import get_reset_password_router
from .auth import get_auth_router
from .users import get_users_router

from app.api.v1.managers import get_user_manager
from app.api.v1.authentication.authenticator import authenticator


if TYPE_CHECKING:
    from fastapi import APIRouter


class UserRouter:
    """
    Main object that ties together the components for user authentication.
    """

    def __init__(self):
        self.get_user_manager = get_user_manager
        self.authenticator = authenticator

    def get_register_router(self) -> "APIRouter":
        """
        Return a router with a register route.
        """
        return get_register_router(self.get_user_manager)

    def get_verify_router(self) -> "APIRouter":
        """
        Return a router with e-mail verification routes.
        """
        return get_verify_router(self.get_user_manager)

    def get_reset_password_router(self) -> "APIRouter":
        """
        Return a reset password process router.
        """
        return get_reset_password_router(self.get_user_manager)

    def get_auth_router(self) -> "APIRouter":
        """
        Return an auth router for a given authentication backend.
        """
        return get_auth_router(
            get_user_manager=self.get_user_manager,
            authenticator=self.authenticator,
        )

    def get_users_router(self) -> "APIRouter":
        """
        Return a router with routes to manage users.
        """
        return get_users_router(
            get_user_manager=self.get_user_manager,
            authenticator=self.authenticator,
        )
