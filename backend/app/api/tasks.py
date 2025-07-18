"""
MediaFlux Hub - Tasks Management API  
Управление задачами публикации
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter()

@router.get("/")
async def get_tasks(status: Optional[str] = None):
    """Получить список задач публикации"""
    tasks = [
        {
            "task_id": "task_001",
            "account": "@lifestyle_vibes_daily",
            "video": "motivation/success_story.mp4",
            "caption": "Секреты успешных людей 💪 #success #motivation",
            "scheduled_time": "2024-01-15 16:30",
            "status": "pending",
            "created": "2024-01-15 14:20"
        },
        {
            "task_id": "task_002", 
            "account": "@business_mindset_pro",
            "video": "business/entrepreneurship_tips.mp4",
            "caption": "3 правила успешного бизнеса 🚀 #business #entrepreneur",
            "scheduled_time": "2024-01-15 18:15",
            "status": "pending",
            "created": "2024-01-15 14:25"
        },
        {
            "task_id": "task_003",
            "account": "@motivation_quotes_hub", 
            "video": "motivation/daily_quotes.mp4",
            "caption": "Вдохновение на каждый день ✨ #motivation #quotes",
            "scheduled_time": "2024-01-15 20:00", 
            "status": "completed",
            "created": "2024-01-15 10:30",
            "completed": "2024-01-15 12:15"
        }
    ]
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "pending": len([t for t in tasks if t["status"] == "pending"]),
        "completed": len([t for t in tasks if t["status"] == "completed"]),
        "failed": len([t for t in tasks if t["status"] == "failed"])
    }

@router.post("/")
async def create_task(task_data: dict):
    """Создать новую задачу публикации"""
    new_task = {
        "task_id": str(uuid.uuid4()),
        "account": task_data["account"],
        "video": task_data["video"],
        "caption": task_data.get("caption", ""),
        "scheduled_time": task_data["scheduled_time"],
        "status": "pending",
        "created": datetime.now().isoformat()
    }
    
    return {
        "message": "Задача успешно создана",
        "task": new_task
    }

@router.get("/schedule")
async def get_schedule():
    """Получить расписание публикаций"""
    return {
        "today": 12,
        "tomorrow": 15,
        "this_week": 89,
        "next_7_days": [
            {"date": "2024-01-15", "posts": 12},
            {"date": "2024-01-16", "posts": 15}, 
            {"date": "2024-01-17", "posts": 18},
            {"date": "2024-01-18", "posts": 14},
            {"date": "2024-01-19", "posts": 16},
            {"date": "2024-01-20", "posts": 20},
            {"date": "2024-01-21", "posts": 11}
        ]
    } 