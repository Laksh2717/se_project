from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
def health_check():
    return {"status": "ok"}
