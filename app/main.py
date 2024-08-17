from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.api.v1.handlers import on_startup, on_shutdown

from app.core.db import adapter
from app.core.config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    await on_startup()
    yield
    # shutdown
    await on_shutdown()
    await adapter.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,  # noqa
        allow_origins=[str(origin).strip("/") for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# First version of API
app.include_router(api_router)
