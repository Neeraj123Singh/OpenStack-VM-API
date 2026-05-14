from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}
