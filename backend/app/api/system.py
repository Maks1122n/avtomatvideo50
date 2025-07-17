"""
MediaFlux Hub - System API
API для системного мониторинга и управления
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.database import SessionLocal
from app.api.auth import verify_token
from app.services.system_service import SystemService

logger = logging.getLogger("mediaflux_hub.system")

router = APIRouter()
system_service = SystemService()

class HealthResponse(BaseModel):
    overall: bool
    timestamp: str
    uptime_seconds: float
    database: dict
    redis: dict
    instagram_api: dict
    disk_space: dict
    memory_usage: dict

class SystemStatsResponse(BaseModel):
    system: dict
    accounts: dict
    posts: dict
    performance: dict
    resources: dict
    content: dict
    top_accounts: List[dict]
    timestamp: str

class LogEntry(BaseModel):
    id: int
    level: str
    message: str
    component: Optional[str]
    account_id: Optional[str]
    task_id: Optional[str]
    details: Optional[str]
    created_at: str

@router.get("/status", response_model=HealthResponse)
async def get_system_status(current_user: dict = Depends(verify_token)):
    """Получение статуса здоровья системы"""
    try:
        health_status = await system_service.get_health_status()
        return HealthResponse(**health_status)
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статуса системы")

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(current_user: dict = Depends(verify_token)):
    """Получение детальной статистики системы"""
    try:
        stats = await system_service.get_system_statistics()
        return SystemStatsResponse(**stats)
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.get("/logs", response_model=List[LogEntry])
async def get_system_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None),
    component: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(verify_token)
):
    """Получение системных логов"""
    try:
        logs = await system_service.get_system_logs(
            limit=limit,
            level=level,
            component=component,
            hours=hours
        )
        return [LogEntry(**log) for log in logs]
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения логов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения логов")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = await system_service.get_health_status()
        return {
            "status": "healthy" if health_status["overall"] else "unhealthy",
            "service": "MediaFlux Hub",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 