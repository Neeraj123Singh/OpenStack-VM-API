from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class VMStatus(str, Enum):
    BUILD = "BUILD"
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    DELETED = "DELETED"
    UNKNOWN = "UNKNOWN"


class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["app-vm-01"])
    image_id: str = Field(..., description="Glance image UUID or name resolvable by the backend")
    flavor_id: str = Field(..., description="Nova flavor UUID or name")
    network_id: str | None = Field(
        default=None,
        description="Optional Neutron network for primary NIC",
    )
    key_name: str | None = Field(default=None, description="SSH keypair name in Nova")
    metadata: dict[str, str] | None = None


class VMResponse(BaseModel):
    id: str
    name: str
    status: VMStatus
    image_id: str | None = None
    flavor_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    addresses: dict[str, list[str]] | None = Field(
        default=None,
        description="Network name -> list of IPs (OpenStack-style)",
    )


class VMListResponse(BaseModel):
    vms: list[VMResponse]
    total: int


class ActionResponse(BaseModel):
    vm_id: str
    action: str
    accepted: bool = True
    message: str | None = None
