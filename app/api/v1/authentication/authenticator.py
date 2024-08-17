import re

from inspect import Parameter, Signature
from typing import Callable, Optional, cast, TYPE_CHECKING

from fastapi import Depends, HTTPException, status

from makefun import with_signature

from app.api.v1.managers import get_user_manager
from app.api.v1.authentication.backend import auth_backend

from app.core.config import settings

if TYPE_CHECKING:
    from app.api.v1.managers import UserManager

    from app.core.models import User


INVALID_CHARS_PATTERN = re.compile(r"[^0-9a-zA-Z_]")
INVALID_LEADING_CHARS_PATTERN = re.compile(r"^[^a-zA-Z_]+")


def name_to_variable_name(name: str, prefix: str) -> str:
    """Transform a backend name string into a string safe to use as variable name."""
    name = re.sub(INVALID_CHARS_PATTERN, "", name)
    name = re.sub(INVALID_LEADING_CHARS_PATTERN, "", name)
    return f"{prefix}_{name}"


class Authenticator:
    """
    Provides dependency callable to retrieve authenticated user with a token.

    It performs authentication based on the specified backend.
    If the backend does not return a user, an HTTPException is thrown.
    """

    def get_current_user_token(
        self,
        required_token_type: str,
        optional: bool = False,
        active: bool = True,
        verified: bool = True,
        superuser: bool = False,
    ):
        """
        Return a dependency callable to retrieve currently authenticated user and token.
        """
        signature = self._get_dependency_signature()

        @with_signature(signature)
        async def current_user_token_dependency(*args, **kwargs):
            return await self._authenticate(
                *args,
                token_type=required_token_type,
                optional=optional,
                active=active,
                verified=verified,
                superuser=superuser,
                **kwargs,
            )

        return current_user_token_dependency

    def get_current_user(
        self,
        optional: bool = False,
        active: bool = True,
        verified: bool = True,
        superuser: bool = False,
    ):
        """
        Return a dependency callable to retrieve currently authenticated user.

        :param optional: If `True`, `None` is returned if there is no authenticated user
        or if it doesn't pass the other requirements.
        Otherwise, throw `401 Unauthorized`. Defaults to `False`.
        Otherwise, an exception is raised. Defaults to `False`.
        :param active: If `True`, throw `401 Unauthorized` if
        the authenticated user is inactive. Defaults to `False`.
        :param verified: If `True`, throw `401 Unauthorized` if
        the authenticated user is not verified. Defaults to `False`.
        :param superuser: If `True`, throw `403 Forbidden` if
        the authenticated user is not a superuser. Defaults to `False`.
        """
        signature = self._get_dependency_signature()

        @with_signature(signature)
        async def current_user_dependency(*args, **kwargs):
            user, _ = await self._authenticate(
                *args,
                token_type=settings.AUTH.ACCESS_TOKEN,
                optional=optional,
                active=active,
                verified=verified,
                superuser=superuser,
                **kwargs,
            )
            return user

        return current_user_dependency

    async def _authenticate(  # noqa
        self,
        *args,  # noqa
        user_manager: "UserManager",
        token_type: str,
        optional: bool,
        active: bool,
        verified: bool,
        superuser: bool,
        **kwargs,
    ) -> tuple[
        Optional["User"],
        tuple[Optional[str], Optional[int]],
    ]:
        user: Optional["User"] = None
        token: Optional[str] = kwargs.get(
            name_to_variable_name(name=auth_backend.name, prefix=token_type)
        )
        token_exp: Optional[int] = None

        if token is not None:
            user, token_exp = await auth_backend.strategy.read_token(
                token=token,
                user_manager=user_manager,
                required_token_type=token_type,
            )

        status_code = status.HTTP_401_UNAUTHORIZED

        if user is not None:
            if active and not user.is_active:
                user = None
            elif (
                verified and not user.is_verified or superuser and not user.is_superuser
            ):
                user = None
                status_code = status.HTTP_403_FORBIDDEN

        if not user and not optional:
            raise HTTPException(status_code=status_code)

        return user, (token, token_exp)

    def _get_dependency_signature(self) -> Signature:  # noqa
        """
        Generate a dynamic signature for the get_current_user dependency.

        This method is redundant for the current API version,
        but I'll keep it for future compatibility.
        """
        parameters: list[Parameter] = [
            Parameter(
                name="user_manager",
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(get_user_manager),
            ),
            Parameter(
                name=name_to_variable_name(
                    name=auth_backend.name, prefix=settings.AUTH.ACCESS_TOKEN
                ),
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(cast(Callable, auth_backend.transport.scheme)),
            ),
            Parameter(
                name=name_to_variable_name(
                    name=auth_backend.name, prefix=settings.AUTH.REFRESH_TOKEN
                ),
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=Depends(auth_backend.transport.get_cookie),
            ),
        ]

        return Signature(parameters)


authenticator = Authenticator()
