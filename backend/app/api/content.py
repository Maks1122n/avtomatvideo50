"""
MediaFlux Hub - Content Management API
Управление видео контентом
"""

from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os

router = APIRouter()

@router.get("/folders")
async def get_content_folders():
    """Список папок с контентом"""
    folders = [
        {
            "id": "motivation",
            "name": "Мотивация",
            "total_videos": 45,
            "used_videos": 23,
            "size": "2.1 GB",
            "last_updated": "2 часа назад"
        },
        {
            "id": "lifestyle", 
            "name": "Лайфстайл",
            "total_videos": 38,
            "used_videos": 15,
            "size": "1.8 GB",
            "last_updated": "1 день назад"
        },
        {
            "id": "business",
            "name": "Бизнес", 
            "total_videos": 29,
            "used_videos": 12,
            "size": "1.3 GB",
            "last_updated": "3 часа назад"
        },
        {
            "id": "entertainment",
            "name": "Развлечения",
            "total_videos": 52,
            "used_videos": 31,
            "size": "2.7 GB", 
            "last_updated": "30 минут назад"
        }
    ]
    return folders

@router.post("/upload")
async def upload_videos(
    videos: List[UploadFile] = File(...),
    category: str = Form(...)
):
    """Загрузка видео файлов"""
    uploaded_files = []
    
    for video in videos:
        # Симуляция сохранения файла
        filename = f"{category}_{video.filename}"
        uploaded_files.append({
            "filename": filename,
            "size": len(await video.read()),
            "category": category
        })
    
    return {
        "success": True,
        "message": f"Загружено {len(videos)} видео",
        "files": uploaded_files
    } 