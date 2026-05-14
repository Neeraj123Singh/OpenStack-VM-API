"""ASGI entrypoint for uvicorn: `uvicorn main:app`."""

from app.main import app

__all__ = ["app"]
