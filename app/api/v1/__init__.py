from fastapi import APIRouter

from app.core.config import settings

from .views import user_router


v1_router = APIRouter(
    prefix=f"{settings.API.V1.PREFIX}",
)


v1_router.include_router(
    router=user_router.get_register_router(),
)
v1_router.include_router(
    router=user_router.get_verify_router(),
)
v1_router.include_router(
    router=user_router.get_reset_password_router(),
)
v1_router.include_router(
    router=user_router.get_auth_router(),
)
v1_router.include_router(
    router=user_router.get_users_router(),
)
