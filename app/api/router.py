from fastapi import APIRouter

from app.api.routes import health, vms

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health")
api_router.include_router(vms.router)
