from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.services.base import VMService
from app.services.mock_vm import MockVMService
from app.services.openstack_vm import OpenStackVMService

_mock_singleton: MockVMService | None = None


def get_vm_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> VMService:
    global _mock_singleton
    if settings.openstack_mode == "mock":
        if _mock_singleton is None:
            _mock_singleton = MockVMService()
        return _mock_singleton
    return OpenStackVMService(settings)
