from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.links import router as links_router
from app.routers.project import router as project_router

__all__ = [
    "auth_router",
    "user_router",
    "links_router",
    "project_router"
]