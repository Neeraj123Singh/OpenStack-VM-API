from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Placeholder for DB pools, telemetry, etc.
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="REST API for OpenStack Nova VM lifecycle (create, list, get, delete, start, stop, reboot).",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
