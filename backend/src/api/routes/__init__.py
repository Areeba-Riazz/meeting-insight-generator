"""API route handlers."""

from fastapi import APIRouter

from . import health, upload, status, insights

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1", tags=["health"])
api_router.include_router(upload.router, prefix="/api/v1", tags=["pipeline"])
api_router.include_router(status.router, prefix="/api/v1", tags=["pipeline"])
api_router.include_router(insights.router, prefix="/api/v1", tags=["pipeline"])

