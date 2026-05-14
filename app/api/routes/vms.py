from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.deps import get_vm_service
from app.exceptions import VMNotFoundError
from app.models.schemas import (
    ActionResponse,
    VMCreateRequest,
    VMListResponse,
    VMResponse,
)
from app.services.base import VMService

router = APIRouter(prefix="/vms", tags=["VMs"])


@router.post("", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    body: VMCreateRequest,
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> VMResponse:
    try:
        return await svc.create_vm(body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e


@router.get("", response_model=VMListResponse)
async def list_vms(
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> VMListResponse:
    try:
        vms = await svc.list_vms()
        return VMListResponse(vms=vms, total=len(vms))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e


@router.get("/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: str,
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> VMResponse:
    try:
        vm = await svc.get_vm(vm_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found")
    return vm


@router.delete("/{vm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vm(
    vm_id: str,
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> None:
    try:
        ok = await svc.delete_vm(vm_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found")


@router.post("/{vm_id}/actions/start", response_model=ActionResponse)
async def start_vm(
    vm_id: str,
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> ActionResponse:
    try:
        await svc.start_vm(vm_id)
    except VMNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found") from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e
    return ActionResponse(vm_id=vm_id, action="start")


@router.post("/{vm_id}/actions/stop", response_model=ActionResponse)
async def stop_vm(
    vm_id: str,
    svc: Annotated[VMService, Depends(get_vm_service)],
) -> ActionResponse:
    try:
        await svc.stop_vm(vm_id)
    except VMNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found") from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e
    return ActionResponse(vm_id=vm_id, action="stop")


@router.post("/{vm_id}/actions/reboot", response_model=ActionResponse)
async def reboot_vm(
    vm_id: str,
    svc: Annotated[VMService, Depends(get_vm_service)],
    hard: Annotated[bool, Query(description="Hard reboot if true")] = False,
) -> ActionResponse:
    try:
        await svc.reboot_vm(vm_id, hard=hard)
    except VMNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VM not found") from None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenStack error: {e!s}",
        ) from e
    return ActionResponse(vm_id=vm_id, action="reboot")
