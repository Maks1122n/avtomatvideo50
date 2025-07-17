"""
MediaFlux Hub - Tasks API
API для управления задачами публикации
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.database import SessionLocal, PostTask, Account
from app.api.auth import verify_token

logger = logging.getLogger("mediaflux_hub.tasks")

router = APIRouter()

class TaskResponse(BaseModel):
    task_id: str
    account_username: str
    video_path: str
    generated_caption: str
    scheduled_time: datetime
    status: str
    attempts: int
    media_id: Optional[str]
    instagram_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(verify_token)
):
    """Получение списка задач публикации"""
    try:
        db = SessionLocal()
        
        query = db.query(PostTask).join(Account)
        
        if status:
            query = query.filter(PostTask.status == status)
        
        tasks = query.order_by(PostTask.scheduled_time.desc()).limit(limit).all()
        
        result = [
            TaskResponse(
                task_id=task.task_id,
                account_username=task.account.username,
                video_path=task.video_path,
                generated_caption=task.generated_caption,
                scheduled_time=task.scheduled_time,
                status=task.status,
                attempts=task.attempts,
                media_id=task.media_id,
                instagram_url=task.instagram_url,
                error_message=task.error_message,
                created_at=task.created_at,
                completed_at=task.completed_at
            )
            for task in tasks
        ]
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения задач: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения задач")

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(verify_token)
):
    """Удаление задачи"""
    try:
        db = SessionLocal()
        
        task = db.query(PostTask).filter(PostTask.task_id == task_id).first()
        if not task:
            db.close()
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        db.delete(task)
        db.commit()
        db.close()
        
        return {"message": "Задача удалена", "deleted_at": datetime.now().isoformat()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка удаления задачи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления задачи") 