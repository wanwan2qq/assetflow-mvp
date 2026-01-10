"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "AssetFlow API"}


@router.get("/db")
async def database_health_check(db: AsyncSession = Depends(get_db_session)):
    """Database connectivity health check"""
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
