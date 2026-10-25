from fastapi import APIRouter

from supportiq.api.v1.endpoints import health, tickets, knowledge

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    tickets.router,
    tags=["Tickets"],
)

api_router.include_router(
    knowledge.router,
    tags=["Knowledge Base"],
)
