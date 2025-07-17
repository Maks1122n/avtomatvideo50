"""
MediaFlux Hub - Content API
API для управления видео контентом
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel

from app.config import settings
from app.database import SessionLocal, ContentFolder
from app.api.auth import verify_token
from app.services.content_service import MediaFluxContentService

logger = logging.getLogger("mediaflux_hub.content")

router = APIRouter()
content_service = MediaFluxContentService()

# Pydantic модели
class FolderResponse(BaseModel):
    folder_id: str
    name: str
    path: str
    total_videos: int
    used_videos: int
    posts_per_week: int
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ContentStats(BaseModel):
    total_folders: int
    active_folders: int
    total_videos: int
    categories: Dict[str, Any]
    top_folders: List[tuple]
    average_videos_per_folder: float


@router.get("/folders", response_model=List[FolderResponse])
async def get_content_folders(current_user: dict = Depends(verify_token)):
    """Получение списка папок с контентом"""
    logger.info(f"📁 MediaFlux Hub: Запрос папок контента от {current_user['username']}")
    
    try:
        db = SessionLocal()
        folders = db.query(ContentFolder).order_by(ContentFolder.created_at.desc()).all()
        
        result = [
            FolderResponse(
                folder_id=folder.folder_id,
                name=folder.name,
                path=folder.path,
                total_videos=folder.total_videos,
                used_videos=folder.used_videos,
                posts_per_week=folder.posts_per_week,
                category=folder.category,
                is_active=folder.is_active,
                created_at=folder.created_at,
                updated_at=folder.updated_at
            )
            for folder in folders
        ]
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения папок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения папок контента")


@router.post("/scan")
async def scan_content_folders(current_user: dict = Depends(verify_token)):
    """Сканирование папок с контентом"""
    logger.info(f"🔍 MediaFlux Hub: Сканирование контента от {current_user['username']}")
    
    try:
        db = SessionLocal()
        folders = await content_service.scan_content_folders(db)
        db.close()
        
        return {
            "message": f"Сканирование завершено. Найдено {len(folders)} папок",
            "folders_count": len(folders),
            "scanned_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка сканирования: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сканирования контента")


@router.get("/stats", response_model=ContentStats)
async def get_content_stats(current_user: dict = Depends(verify_token)):
    """Получение статистики контента"""
    try:
        db = SessionLocal()
        stats = await content_service.get_content_statistics(db)
        db.close()
        
        return ContentStats(**stats)
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики контента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.delete("/folders/{folder_id}")
async def delete_content_folder(
    folder_id: str,
    current_user: dict = Depends(verify_token)
):
    """Удаление папки контента"""
    logger.info(f"🗑️ MediaFlux Hub: Удаление папки {folder_id}")
    
    try:
        db = SessionLocal()
        
        folder = db.query(ContentFolder).filter(ContentFolder.folder_id == folder_id).first()
        if not folder:
            db.close()
            raise HTTPException(status_code=404, detail="Папка не найдена")
        
        folder_name = folder.name
        db.delete(folder)
        db.commit()
        db.close()
        
        return {
            "message": f"Папка {folder_name} удалена",
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка удаления папки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления папки") 