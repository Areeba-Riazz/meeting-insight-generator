"""API route handlers."""

from fastapi import APIRouter

from . import health, upload, status, insights, search, projects, project_meetings, chat

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1", tags=["health"])
api_router.include_router(projects.router, prefix="/api/v1", tags=["projects"])
api_router.include_router(
    project_meetings.router, prefix="/api/v1", tags=["project-meetings"]
)
api_router.include_router(upload.router, prefix="/api/v1", tags=["pipeline"])
api_router.include_router(status.router, prefix="/api/v1", tags=["pipeline"])
api_router.include_router(insights.router, prefix="/api/v1", tags=["pipeline"])
api_router.include_router(search.router, prefix="/api/v1", tags=["search"])
api_router.include_router(chat.router, prefix="/api/v1", tags=["chat"])

