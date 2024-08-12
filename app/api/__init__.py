from fastapi import APIRouter

from app.core.config import settings

from .v1 import v1_router


api_router = APIRouter(
    prefix=f"{settings.API.PREFIX}",
)

api_router.include_router(v1_router)
