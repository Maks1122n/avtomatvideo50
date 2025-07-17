"""
MediaFlux Hub - Proxies API
API для управления прокси-серверами
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.database import SessionLocal, Proxy
from app.api.auth import verify_token
from app.services.proxy_service import ProxyManager

logger = logging.getLogger("mediaflux_hub.proxies")

router = APIRouter()
proxy_manager = ProxyManager()

class ProxyResponse(BaseModel):
    id: int
    proxy_url: str
    country: Optional[str]
    city: Optional[str]
    is_active: bool
    error_count: int
    max_errors: int
    last_used: Optional[datetime]
    accounts_assigned: int
    max_accounts: int
    created_at: datetime
    updated_at: datetime

class ProxyStats(BaseModel):
    total: int
    active: int
    assigned: int
    available: int
    countries: Dict[str, Any]
    utilization: float

@router.get("/", response_model=List[ProxyResponse])
async def get_proxies(
    is_active: Optional[bool] = Query(None),
    country: Optional[str] = Query(None),
    current_user: dict = Depends(verify_token)
):
    """Получение списка прокси"""
    try:
        db = SessionLocal()
        
        query = db.query(Proxy)
        
        if is_active is not None:
            query = query.filter(Proxy.is_active == is_active)
        
        if country:
            query = query.filter(Proxy.country == country)
        
        proxies = query.order_by(Proxy.created_at.desc()).all()
        
        result = [
            ProxyResponse(
                id=proxy.id,
                proxy_url=proxy.proxy_url,
                country=proxy.country,
                city=proxy.city,
                is_active=proxy.is_active,
                error_count=proxy.error_count,
                max_errors=proxy.max_errors,
                last_used=proxy.last_used,
                accounts_assigned=proxy.accounts_assigned,
                max_accounts=proxy.max_accounts,
                created_at=proxy.created_at,
                updated_at=proxy.updated_at
            )
            for proxy in proxies
        ]
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения прокси: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка прокси")

@router.post("/sync")
async def sync_proxies(current_user: dict = Depends(verify_token)):
    """Синхронизация прокси из файла"""
    try:
        await proxy_manager.sync_proxies_to_database()
        return {
            "message": "Синхронизация прокси завершена",
            "synced_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка синхронизации прокси: {e}")
        raise HTTPException(status_code=500, detail="Ошибка синхронизации прокси")

@router.post("/test")
async def test_all_proxies(current_user: dict = Depends(verify_token)):
    """Тестирование всех прокси"""
    try:
        results = await proxy_manager.test_all_proxies()
        working_count = sum(1 for is_working in results.values() if is_working)
        
        return {
            "message": f"Тестирование завершено. Работающих: {working_count}/{len(results)}",
            "working_proxies": working_count,
            "total_proxies": len(results),
            "tested_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка тестирования прокси: {e}")
        raise HTTPException(status_code=500, detail="Ошибка тестирования прокси")

@router.get("/stats", response_model=ProxyStats)
async def get_proxy_stats(current_user: dict = Depends(verify_token)):
    """Получение статистики прокси"""
    try:
        stats = await proxy_manager.get_proxy_statistics()
        return ProxyStats(**stats)
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики прокси: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.delete("/{proxy_id}")
async def delete_proxy(
    proxy_id: int,
    current_user: dict = Depends(verify_token)
):
    """Удаление прокси"""
    try:
        db = SessionLocal()
        
        proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
        if not proxy:
            db.close()
            raise HTTPException(status_code=404, detail="Прокси не найден")
        
        proxy_url = proxy.proxy_url
        db.delete(proxy)
        db.commit()
        db.close()
        
        return {
            "message": f"Прокси {proxy_url} удален",
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка удаления прокси: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления прокси") 