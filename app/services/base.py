from abc import ABC, abstractmethod

from app.models.schemas import VMCreateRequest, VMResponse


class VMService(ABC):
    @abstractmethod
    async def create_vm(self, req: VMCreateRequest) -> VMResponse:
        pass

    @abstractmethod
    async def list_vms(self) -> list[VMResponse]:
        pass

    @abstractmethod
    async def get_vm(self, vm_id: str) -> VMResponse | None:
        pass

    @abstractmethod
    async def delete_vm(self, vm_id: str) -> bool:
        pass

    @abstractmethod
    async def start_vm(self, vm_id: str) -> None:
        pass

    @abstractmethod
    async def stop_vm(self, vm_id: str) -> None:
        pass

    @abstractmethod
    async def reboot_vm(self, vm_id: str, hard: bool = False) -> None:
        pass
