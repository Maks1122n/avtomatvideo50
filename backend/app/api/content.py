"""
MediaFlux Hub - Content Management API
Управление видео контентом
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/folders")
async def get_content_folders():
    """Получить список папок с контентом"""
    folders = [
        {
            "name": "motivation",
            "display_name": "Мотивация",
            "video_count": 23,
            "total_size": "450 MB",
            "last_upload": "2 часа назад",
            "status": "active"
        },
        {
            "name": "business", 
            "display_name": "Бизнес",
            "video_count": 18,
            "total_size": "320 MB",
            "last_upload": "5 часов назад",
            "status": "active"
        },
        {
            "name": "lifestyle",
            "display_name": "Лайфстайл", 
            "video_count": 31,
            "total_size": "580 MB",
            "last_upload": "1 час назад",
            "status": "active"
        },
        {
            "name": "entertainment",
            "display_name": "Развлечения",
            "video_count": 15,
            "total_size": "280 MB", 
            "last_upload": "6 часов назад",
            "status": "active"
        }
    ]
    
    return {
        "folders": folders,
        "total_videos": sum(f["video_count"] for f in folders),
        "total_size": "1.63 GB"
    }

@router.get("/videos")
async def get_videos(folder: Optional[str] = None):
    """Получить список видео файлов"""
    videos = [
        {
            "id": "video_001",
            "filename": "success_mindset_tips.mp4",
            "folder": "motivation",
            "size": "15.2 MB",
            "duration": "0:45",
            "uploaded": "2024-01-15 14:30",
            "used_count": 5,
            "last_used": "1 час назад",
            "status": "available"
        },
        {
            "id": "video_002", 
            "filename": "entrepreneurship_basics.mp4",
            "folder": "business",
            "size": "22.8 MB",
            "duration": "1:20",
            "uploaded": "2024-01-15 12:15",
            "used_count": 3,
            "last_used": "3 часа назад",
            "status": "available"
        },
        {
            "id": "video_003",
            "filename": "morning_routine.mp4", 
            "folder": "lifestyle",
            "size": "18.5 MB",
            "duration": "1:05",
            "uploaded": "2024-01-15 09:45",
            "used_count": 7,
            "last_used": "30 минут назад",
            "status": "available"
        }
    ]
    
    if folder:
        videos = [v for v in videos if v["folder"] == folder]
    
    return videos

@router.post("/upload")
async def upload_video(video_data: dict):
    """Загрузить новое видео"""
    # Симуляция загрузки
    return {
        "message": "Видео успешно загружено",
        "video_id": str(uuid.uuid4()),
        "filename": video_data.get("filename", "new_video.mp4"),
        "status": "processing"
    } 