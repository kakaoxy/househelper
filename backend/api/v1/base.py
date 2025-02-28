from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings

router = APIRouter(tags=["base"])

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行正常"}

@router.get("/info")
async def api_info():
    """API信息接口"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "description": settings.PROJECT_DESCRIPTION
    }