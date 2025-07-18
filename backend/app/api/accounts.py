from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid

router = APIRouter()

class AccountCreate(BaseModel):
    username: str
    access_token: str
    account_id: str
    proxy: str = None
    daily_limit: int = 5

class Account(BaseModel):
    id: str
    username: str
    status: str
    posts_today: int
    last_activity: str
    proxy_status: str
    daily_limit: int
    total_posts: int

@router.get("/", response_model=List[Account])
async def list_accounts():
    """Список всех аккаунтов"""
    demo_accounts = [
        {
            "id": "1",
            "username": "demo_instagram_fashion",
            "status": "active",
            "posts_today": 3,
            "last_activity": "2 часа назад",
            "proxy_status": "connected",
            "daily_limit": 5,
            "total_posts": 247
        },
        {
            "id": "2", 
            "username": "demo_lifestyle_blog",
            "status": "active",
            "posts_today": 2,
            "last_activity": "1 час назад", 
            "proxy_status": "connected",
            "daily_limit": 8,
            "total_posts": 189
        },
        {
            "id": "3",
            "username": "demo_business_tips",
            "status": "limited",
            "posts_today": 5,
            "last_activity": "30 минут назад",
            "proxy_status": "warning", 
            "daily_limit": 5,
            "total_posts": 356
        }
    ]
    return demo_accounts

@router.post("/", response_model=dict)
async def add_account(account: AccountCreate):
    """Добавить новый аккаунт"""
    # Симуляция добавления аккаунта
    new_id = str(uuid.uuid4())
    return {
        "success": True,
        "message": "Аккаунт успешно добавлен",
        "account_id": new_id
    }

@router.post("/test")
async def test_connection(account_data: dict):
    """Тестирование соединения с Instagram API"""
    # Симуляция тестирования
    import time
    time.sleep(2)  # Имитация проверки
    
    return {
        "success": True,
        "message": "Соединение установлено успешно",
        "account_info": {
            "username": account_data.get("username", ""),
            "followers": 12500,
            "following": 890,
            "posts": 156
        }
    } 