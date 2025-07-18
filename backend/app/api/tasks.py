"""
MediaFlux Hub - Tasks Management API  
Управление задачами публикации
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/")
async def get_tasks():
    """Список задач публикации"""
    tasks = []
    
    for i in range(10):
        task_time = datetime.now() + timedelta(hours=random.randint(1, 24))
        tasks.append({
            "id": f"task_{i+1}",
            "account": f"@demo_account_{i%3+1}",
            "video": f"motivation/video_{i+1}.mp4",
            "scheduled_time": task_time.strftime("%H:%M %d.%m"),
            "status": random.choice(["pending", "scheduled", "completed"]),
            "caption": f"Мотивационный пост #{i+1}"
        })
    
    return tasks

@router.post("/generate-schedule")
async def generate_schedule(schedule_data: dict):
    """Генерация расписания публикаций"""
    return {
        "success": True,
        "message": "Расписание создано успешно",
        "tasks_created": 21,
        "period": schedule_data.get("period", "week")
    } 