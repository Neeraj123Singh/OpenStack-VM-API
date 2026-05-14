from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.exceptions import VMNotFoundError
from app.models.schemas import VMCreateRequest, VMResponse, VMStatus
from app.services.base import VMService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MockVMService(VMService):
    """In-memory VM store for demos and automated tests without a cloud."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._vms: dict[str, VMResponse] = {}

    async def create_vm(self, req: VMCreateRequest) -> VMResponse:
        vm_id = str(uuid.uuid4())
        now = _utcnow()
        vm = VMResponse(
            id=vm_id,
            name=req.name,
            status=VMStatus.BUILD,
            image_id=req.image_id,
            flavor_id=req.flavor_id,
            created_at=now,
            updated_at=now,
            addresses={},
        )
        async with self._lock:
            self._vms[vm_id] = vm

        async def _activate() -> None:
            await asyncio.sleep(0.05)
            async with self._lock:
                if vm_id in self._vms:
                    cur = self._vms[vm_id]
                    self._vms[vm_id] = cur.model_copy(
                        update={
                            "status": VMStatus.ACTIVE,
                            "updated_at": _utcnow(),
                            "addresses": {"private": [f"10.0.0.{hash(vm_id) % 200 + 10}"]},
                        }
                    )

        asyncio.create_task(_activate())
        return vm

    async def list_vms(self) -> list[VMResponse]:
        async with self._lock:
            return list(self._vms.values())

    async def get_vm(self, vm_id: str) -> VMResponse | None:
        async with self._lock:
            return self._vms.get(vm_id)

    async def delete_vm(self, vm_id: str) -> bool:
        async with self._lock:
            if vm_id not in self._vms:
                return False
            del self._vms[vm_id]
            return True

    async def start_vm(self, vm_id: str) -> None:
        async with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                raise VMNotFoundError(vm_id)
            if vm.status == VMStatus.ACTIVE:
                return
            self._vms[vm_id] = vm.model_copy(
                update={"status": VMStatus.ACTIVE, "updated_at": _utcnow()}
            )

    async def stop_vm(self, vm_id: str) -> None:
        async with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                raise VMNotFoundError(vm_id)
            self._vms[vm_id] = vm.model_copy(
                update={"status": VMStatus.STOPPED, "updated_at": _utcnow()}
            )

    async def reboot_vm(self, vm_id: str, hard: bool = False) -> None:
        async with self._lock:
            vm = self._vms.get(vm_id)
            if not vm:
                raise VMNotFoundError(vm_id)
            self._vms[vm_id] = vm.model_copy(
                update={"status": VMStatus.ACTIVE, "updated_at": _utcnow()}
            )
