from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.config import Settings, get_settings
from app.exceptions import VMNotFoundError
from app.models.schemas import VMCreateRequest, VMResponse, VMStatus
from app.services.base import VMService

if TYPE_CHECKING:
    from openstack.connection import Connection


def _map_os_status(status: str | None) -> VMStatus:
    if not status:
        return VMStatus.UNKNOWN
    s = status.upper()
    mapping = {
        "ACTIVE": VMStatus.ACTIVE,
        "BUILD": VMStatus.BUILD,
        "ERROR": VMStatus.ERROR,
        "DELETED": VMStatus.DELETED,
        "SHUTOFF": VMStatus.STOPPED,
        "STOPPED": VMStatus.STOPPED,
        "SHELVED": VMStatus.STOPPED,
        "SHELVED_OFFLOADED": VMStatus.STOPPED,
    }
    return mapping.get(s, VMStatus.UNKNOWN)


def _server_to_vm(server: object) -> VMResponse:
    """Map openstacksdk Server object to API model."""
    image_id = getattr(server, "image_id", None) or (
        (server.image or {}).get("id") if getattr(server, "image", None) else None
    )
    flavor_id = getattr(server, "flavor_id", None) or (
        (server.flavor or {}).get("id") if getattr(server, "flavor", None) else None
    )
    addrs: dict[str, list[str]] | None = None
    raw = getattr(server, "addresses", None) or {}
    if isinstance(raw, dict) and raw:
        addrs = {k: [a.get("addr", str(a)) for a in v] for k, v in raw.items() if isinstance(v, list)}

    created = getattr(server, "created_at", None)
    updated = getattr(server, "updated_at", None)

    def _parse_dt(val: object) -> datetime | None:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
        if isinstance(val, str):
            try:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                return dt
            except ValueError:
                return None
        return None

    return VMResponse(
        id=str(getattr(server, "id", "")),
        name=str(getattr(server, "name", "")),
        status=_map_os_status(getattr(server, "status", None)),
        image_id=str(image_id) if image_id else None,
        flavor_id=str(flavor_id) if flavor_id else None,
        created_at=_parse_dt(created),
        updated_at=_parse_dt(updated),
        addresses=addrs,
    )


class OpenStackVMService(VMService):
    """Nova-backed implementation using openstacksdk (OS_* / clouds.yaml)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._conn: Connection | None = None

    def _get_connection(self) -> Connection:
        if self._conn is not None:
            return self._conn
        import openstack

        kwargs: dict[str, object] = {}
        if self._settings.openstack_project_id:
            kwargs["project_id"] = self._settings.openstack_project_id
        self._conn = openstack.connect(cloud="envvars", **kwargs)
        return self._conn

    async def create_vm(self, req: VMCreateRequest) -> VMResponse:
        def _create() -> VMResponse:
            conn = self._get_connection()
            kwargs: dict[str, object] = {
                "name": req.name,
                "image_id": req.image_id,
                "flavor_id": req.flavor_id,
            }
            if req.key_name:
                kwargs["key_name"] = req.key_name
            if req.metadata:
                kwargs["metadata"] = req.metadata
            if req.network_id:
                kwargs["networks"] = [{"uuid": req.network_id}]
            server = conn.compute.create_server(**kwargs)
            server = conn.compute.wait_for_server(server)
            return _server_to_vm(server)

        return await asyncio.to_thread(_create)

    async def list_vms(self) -> list[VMResponse]:
        def _list() -> list[VMResponse]:
            conn = self._get_connection()
            return [_server_to_vm(s) for s in conn.compute.servers(details=True)]

        return await asyncio.to_thread(_list)

    async def get_vm(self, vm_id: str) -> VMResponse | None:
        def _get() -> VMResponse | None:
            conn = self._get_connection()
            try:
                s = conn.compute.get_server(vm_id)
            except Exception:
                return None
            return _server_to_vm(s) if s else None

        return await asyncio.to_thread(_get)

    async def delete_vm(self, vm_id: str) -> bool:
        def _delete() -> bool:
            from openstack.exceptions import ResourceNotFound

            conn = self._get_connection()
            try:
                s = conn.compute.get_server(vm_id)
            except ResourceNotFound:
                return False
            except Exception:
                return False
            if not s:
                return False
            try:
                conn.compute.delete_server(vm_id, ignore_missing=False)
            except Exception:
                return False
            return True

        return await asyncio.to_thread(_delete)

    async def start_vm(self, vm_id: str) -> None:
        def _start() -> None:
            from openstack.exceptions import ResourceNotFound

            conn = self._get_connection()
            try:
                conn.compute.start_server(vm_id)
            except ResourceNotFound as e:
                raise VMNotFoundError(vm_id) from e

        await asyncio.to_thread(_start)

    async def stop_vm(self, vm_id: str) -> None:
        def _stop() -> None:
            from openstack.exceptions import ResourceNotFound

            conn = self._get_connection()
            try:
                conn.compute.stop_server(vm_id)
            except ResourceNotFound as e:
                raise VMNotFoundError(vm_id) from e

        await asyncio.to_thread(_stop)

    async def reboot_vm(self, vm_id: str, hard: bool = False) -> None:
        def _reboot() -> None:
            from openstack.exceptions import ResourceNotFound

            conn = self._get_connection()
            try:
                conn.compute.reboot_server(vm_id, reboot_type="HARD" if hard else "SOFT")
            except ResourceNotFound as e:
                raise VMNotFoundError(vm_id) from e

        await asyncio.to_thread(_reboot)
