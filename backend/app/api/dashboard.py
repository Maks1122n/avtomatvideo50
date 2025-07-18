from fastapi import APIRouter
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats():
    """Статистика для дашборда"""
    return {
        "total_accounts": 12,
        "active_accounts": 10,
        "posts_today": 47,
        "posts_scheduled": 23,
        "total_views": 89500,
        "total_posts": 256,
        "automation_status": "active",
        "system_health": "healthy",
        "success_rate": 96.5,
        "proxies_active": 8
    }

@router.get("/recent-activity")
async def get_recent_activity():
    """Последние действия системы"""
    activities = [
        {
            "id": 1,
            "time": "2 минуты назад",
            "action": "Публикация завершена",
            "account": "@lifestyle_vibes_daily",
            "status": "success",
            "type": "post",
            "details": "motivation/success_story.mp4"
        },
        {
            "id": 2,
            "time": "5 минут назад",
            "action": "Видео загружено",
            "details": "business/entrepreneurship_tips.mp4",
            "status": "info",
            "type": "upload",
            "account": "system"
        },
        {
            "id": 3,
            "time": "8 минут назад",
            "action": "Новое расписание создано",
            "details": "15 публикаций на завтра",
            "status": "info",
            "type": "schedule",
            "account": "scheduler"
        },
        {
            "id": 4,
            "time": "12 минут назад",
            "action": "Публикация завершена",
            "account": "@business_mindset_pro",
            "status": "success",
            "type": "post",
            "details": "business/leadership_quotes.mp4"
        },
        {
            "id": 5,
            "time": "18 минут назад",
            "action": "Прокси переключен",
            "details": "proxy-us-east-01 → proxy-eu-west-02",
            "status": "warning",
            "type": "proxy",
            "account": "@fashion_trends_2024"
        },
        {
            "id": 6,
            "time": "25 минут назад",
            "action": "Аккаунт добавлен",
            "account": "@entertainment_hub_new",
            "status": "success",
            "type": "account",
            "details": "Настройка завершена"
        }
    ]
    
    return activities

@router.get("/performance")
async def get_performance_data():
    """Данные производительности системы"""
    # Генерируем данные за последние 7 дней
    days = []
    base_date = datetime.now() - timedelta(days=6)
    
    for i in range(7):
        date = base_date + timedelta(days=i)
        days.append({
            "date": date.strftime("%Y-%m-%d"),
            "posts": random.randint(35, 55),
            "views": random.randint(8000, 15000),
            "engagement": random.randint(400, 800)
        })
    
    return {
        "daily_stats": days,
        "total_engagement": 4250,
        "avg_views_per_post": 1200,
        "top_performing_category": "motivation"
    }

@router.get("/system-status")
async def get_system_status():
    """Статус системы и сервисов"""
    return {
        "database": {"status": "healthy", "response_time": "12ms"},
        "redis": {"status": "healthy", "response_time": "3ms"},
        "instagram_api": {"status": "healthy", "rate_limit": "85%"},
        "proxy_pool": {"status": "healthy", "active_proxies": 8, "total_proxies": 10},
        "scheduler": {"status": "active", "next_run": "14:30"},
        "uptime": "7d 14h 32m",
        "memory_usage": "67%",
        "cpu_usage": "23%"
    } 