
from fastapi import APIRouter

from supportiq.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
    }
