from fastapi import FastAPI

from supportiq.api.router import api_router
from supportiq.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)