from fastapi import APIRouter

from supportiq.api.v1.endpoints import health, tickets

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    tickets.router,
    tags=["Tickets"]
)