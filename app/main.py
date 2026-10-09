from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.users import router as users_router
from app.core.config import settings
from app.core.security_headers import SecurityHeadersMiddleware

app = FastAPI(title=settings.app_name)

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(users_router)
