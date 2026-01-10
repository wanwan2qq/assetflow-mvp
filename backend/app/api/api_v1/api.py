"""
API v1 router
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    assets,
    auth,
    chat,
    health,
    profiles,
    recommendations,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
