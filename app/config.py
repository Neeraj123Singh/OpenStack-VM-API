from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OpenStack VM Lifecycle API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # mock: in-memory VMs for demos/tests; real: OpenStack SDK
    openstack_mode: Literal["mock", "real"] = "mock"

    # Optional: restrict operations to a single project when set
    openstack_project_id: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
