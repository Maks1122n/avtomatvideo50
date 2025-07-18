from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats():
    """Статистика для дашборда"""
    return {
        "total_accounts": 4,
        "active_accounts": 3,
        "posts_today": 28,
        "total_views": 62000,
        "posts_scheduled": 45,
        "automation_status": "active",
        "system_health": "healthy",
        "success_rate": 98.5,
        "errors_count": 2
    }

@router.get("/system-status")
async def get_system_status():
    """Статус системы"""
    return {
        "status": "online",
        "uptime": "12h 34m",
        "memory_usage": 45.2,
        "cpu_usage": 23.1,
        "disk_usage": 67.8,
        "active_tasks": 12,
        "queue_size": 8,
        "last_update": datetime.now().isoformat()
    }

@router.get("/recent-activity")
async def get_recent_activity():
    """Последние действия системы"""
    activities = [
        {
            "id": 1,
            "time": "2 минуты назад",
            "action": "Опубликован Reel",
            "account": "@fashion_style",
            "status": "success",
            "details": "motivation/video_001.mp4"
        },
        {
            "id": 2,
            "time": "5 минут назад",
            "action": "Загружено видео",
            "account": "Система",
            "status": "info",
            "details": "lifestyle/new_video.mp4"
        },
        {
            "id": 3,
            "time": "10 минут назад",
            "action": "Запланирована публикация",
            "account": "@business_pro",
            "status": "scheduled",
            "details": "14:30 сегодня"
        },
        {
            "id": 4,
            "time": "15 минут назад",
            "action": "Проверка прокси",
            "account": "Система",
            "status": "warning",
            "details": "Прокси server1 требует проверки"
        }
    ]
    return activities 