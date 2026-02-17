from fastapi import APIRouter

from ..schemas import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Simple liveness endpoint.
    """
    return HealthResponse(status="ok")

