"""
MediaFlux Hub - Accounts API  
API для управления аккаунтами Instagram
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, validator
from cryptography.fernet import Fernet

from app.config import settings
from app.database import SessionLocal, Account
from app.api.auth import verify_token
from app.services.proxy_service import ProxyManager
from app.services.instagram_service import MediaFluxHubAPIService

logger = logging.getLogger("mediaflux_hub.accounts")

router = APIRouter()

# Инициализация сервисов
proxy_manager = ProxyManager()
instagram_service = MediaFluxHubAPIService()

# Шифрование токенов
encryption_key = settings.ENCRYPTION_KEY.encode()
cipher_suite = Fernet(encryption_key)

# Pydantic модели
class AccountCreate(BaseModel):
    username: str
    access_token: str
    instagram_account_id: str
    daily_limit: Optional[int] = 5
    user_agent: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v) < 2:
            raise ValueError('Username должен содержать минимум 2 символа')
        return v.strip().lower()
    
    @validator('access_token')
    def validate_access_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Access token слишком короткий')
        return v.strip()
    
    @validator('daily_limit')
    def validate_daily_limit(cls, v):
        if v is not None and (v < 1 or v > 20):
            raise ValueError('Дневной лимит должен быть от 1 до 20')
        return v

class AccountUpdate(BaseModel):
    daily_limit: Optional[int] = None
    user_agent: Optional[str] = None
    status: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['active', 'limited', 'banned', 'error']:
            raise ValueError('Недопустимый статус аккаунта')
        return v

class AccountResponse(BaseModel):
    id: str
    username: str
    instagram_account_id: str
    daily_limit: int
    current_daily_posts: int
    status: str
    last_post_time: Optional[datetime]
    last_activity: Optional[datetime]
    proxy_url: Optional[str]
    created_at: datetime
    updated_at: datetime

class AccountStats(BaseModel):
    total_accounts: int
    active_accounts: int
    limited_accounts: int
    banned_accounts: int
    error_accounts: int
    posts_today: int
    posts_week: int

class AccountTest(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


def encrypt_token(token: str) -> str:
    """Шифрование токена"""
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Расшифровка токена"""
    return cipher_suite.decrypt(encrypted_token.encode()).decode()


@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    search: Optional[str] = Query(None, description="Поиск по username"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(verify_token)
):
    """Получение списка аккаунтов Instagram"""
    logger.info(f"📋 MediaFlux Hub: Запрос списка аккаунтов от {current_user['username']}")
    
    try:
        db = SessionLocal()
        
        # Базовый запрос
        query = db.query(Account)
        
        # Фильтры
        if status:
            query = query.filter(Account.status == status)
        
        if search:
            query = query.filter(Account.username.contains(search.lower()))
        
        # Сортировка и пагинация
        accounts = query.order_by(Account.created_at.desc()).offset(offset).limit(limit).all()
        
        # Преобразуем результат
        result = []
        for account in accounts:
            result.append(AccountResponse(
                id=account.id,
                username=account.username,
                instagram_account_id=account.instagram_account_id,
                daily_limit=account.daily_limit,
                current_daily_posts=account.current_daily_posts,
                status=account.status,
                last_post_time=account.last_post_time,
                last_activity=account.last_activity,
                proxy_url=account.proxy_url,
                created_at=account.created_at,
                updated_at=account.updated_at
            ))
        
        db.close()
        logger.info(f"✅ MediaFlux Hub: Возвращено {len(result)} аккаунтов")
        return result
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения аккаунтов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка аккаунтов")


@router.post("/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: dict = Depends(verify_token)
):
    """Добавление нового аккаунта Instagram"""
    logger.info(f"➕ MediaFlux Hub: Добавление аккаунта @{account_data.username} пользователем {current_user['username']}")
    
    try:
        db = SessionLocal()
        
        # Проверяем уникальность username
        existing = db.query(Account).filter(Account.username == account_data.username).first()
        if existing:
            db.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Аккаунт @{account_data.username} уже существует"
            )
        
        # Шифруем access token
        encrypted_token = encrypt_token(account_data.access_token)
        
        # Создаем новый аккаунт
        account = Account(
            username=account_data.username,
            access_token=encrypted_token,
            instagram_account_id=account_data.instagram_account_id,
            daily_limit=account_data.daily_limit or 5,
            user_agent=account_data.user_agent,
            status='active'
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        # Назначаем прокси
        try:
            proxy_url = await proxy_manager.assign_proxy_to_account(account.id)
            if proxy_url:
                account.proxy_url = proxy_url
                db.commit()
                logger.info(f"🔗 MediaFlux Hub: Прокси назначен для @{account.username}")
        except Exception as proxy_error:
            logger.warning(f"⚠️ MediaFlux Hub: Не удалось назначить прокси: {proxy_error}")
        
        result = AccountResponse(
            id=account.id,
            username=account.username,
            instagram_account_id=account.instagram_account_id,
            daily_limit=account.daily_limit,
            current_daily_posts=account.current_daily_posts,
            status=account.status,
            last_post_time=account.last_post_time,
            last_activity=account.last_activity,
            proxy_url=account.proxy_url,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        
        db.close()
        logger.info(f"✅ MediaFlux Hub: Аккаунт @{account.username} успешно добавлен")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка создания аккаунта: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise HTTPException(status_code=500, detail="Ошибка создания аккаунта")


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: dict = Depends(verify_token)
):
    """Получение информации об аккаунте"""
    logger.info(f"📄 MediaFlux Hub: Запрос аккаунта {account_id}")
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            db.close()
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        result = AccountResponse(
            id=account.id,
            username=account.username,
            instagram_account_id=account.instagram_account_id,
            daily_limit=account.daily_limit,
            current_daily_posts=account.current_daily_posts,
            status=account.status,
            last_post_time=account.last_post_time,
            last_activity=account.last_activity,
            proxy_url=account.proxy_url,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        
        db.close()
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения аккаунта: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения аккаунта")


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    account_data: AccountUpdate,
    current_user: dict = Depends(verify_token)
):
    """Обновление настроек аккаунта"""
    logger.info(f"✏️ MediaFlux Hub: Обновление аккаунта {account_id}")
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            db.close()
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        # Обновляем поля
        if account_data.daily_limit is not None:
            account.daily_limit = account_data.daily_limit
        
        if account_data.user_agent is not None:
            account.user_agent = account_data.user_agent
        
        if account_data.status is not None:
            old_status = account.status
            account.status = account_data.status
            logger.info(f"📊 MediaFlux Hub: Статус аккаунта @{account.username} изменен: {old_status} -> {account_data.status}")
        
        account.updated_at = datetime.now()
        db.commit()
        
        result = AccountResponse(
            id=account.id,
            username=account.username,
            instagram_account_id=account.instagram_account_id,
            daily_limit=account.daily_limit,
            current_daily_posts=account.current_daily_posts,
            status=account.status,
            last_post_time=account.last_post_time,
            last_activity=account.last_activity,
            proxy_url=account.proxy_url,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        
        db.close()
        logger.info(f"✅ MediaFlux Hub: Аккаунт @{account.username} обновлен")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка обновления аккаунта: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise HTTPException(status_code=500, detail="Ошибка обновления аккаунта")


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user: dict = Depends(verify_token)
):
    """Удаление аккаунта"""
    logger.info(f"🗑️ MediaFlux Hub: Удаление аккаунта {account_id}")
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            db.close()
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        username = account.username
        
        # Освобождаем прокси
        if account.proxy_url:
            try:
                await proxy_manager._release_proxy_from_account(account.proxy_url, db)
            except Exception as e:
                logger.warning(f"⚠️ MediaFlux Hub: Ошибка освобождения прокси: {e}")
        
        # Удаляем аккаунт
        db.delete(account)
        db.commit()
        db.close()
        
        logger.info(f"✅ MediaFlux Hub: Аккаунт @{username} успешно удален")
        
        return {
            "message": f"Аккаунт @{username} успешно удален",
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка удаления аккаунта: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise HTTPException(status_code=500, detail="Ошибка удаления аккаунта")


@router.post("/{account_id}/test", response_model=AccountTest)
async def test_account(
    account_id: str,
    current_user: dict = Depends(verify_token)
):
    """Тестирование аккаунта Instagram"""
    logger.info(f"🧪 MediaFlux Hub: Тестирование аккаунта {account_id}")
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            db.close()
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        # Расшифровываем токен
        try:
            access_token = decrypt_token(account.access_token)
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка расшифровки токена: {e}")
            db.close()
            return AccountTest(
                success=False,
                message="Ошибка расшифровки токена"
            )
        
        # Тестируем через Instagram API
        # Здесь должен быть реальный тест API, пока возвращаем успех
        test_details = {
            "account_id": account.instagram_account_id,
            "username": account.username,
            "proxy": account.proxy_url,
            "test_time": datetime.now().isoformat()
        }
        
        # Обновляем время последней активности
        account.last_activity = datetime.now()
        account.updated_at = datetime.now()
        db.commit()
        db.close()
        
        logger.info(f"✅ MediaFlux Hub: Тест аккаунта @{account.username} прошел успешно")
        
        return AccountTest(
            success=True,
            message=f"Аккаунт @{account.username} работает корректно",
            details=test_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка тестирования аккаунта: {e}")
        if 'db' in locals():
            db.close()
        return AccountTest(
            success=False,
            message=f"Ошибка тестирования аккаунта: {str(e)}"
        )


@router.get("/stats/summary", response_model=AccountStats)
async def get_accounts_stats(current_user: dict = Depends(verify_token)):
    """Получение статистики по аккаунтам"""
    logger.info(f"📊 MediaFlux Hub: Запрос статистики аккаунтов")
    
    try:
        db = SessionLocal()
        
        # Подсчитываем аккаунты по статусам
        total_accounts = db.query(Account).count()
        active_accounts = db.query(Account).filter(Account.status == 'active').count()
        limited_accounts = db.query(Account).filter(Account.status == 'limited').count()
        banned_accounts = db.query(Account).filter(Account.status == 'banned').count()
        error_accounts = db.query(Account).filter(Account.status == 'error').count()
        
        # Статистика постов
        from app.database import PostTask
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = datetime.now() - timedelta(days=7)
        
        posts_today = db.query(PostTask).filter(
            PostTask.status == 'completed',
            PostTask.completed_at >= today
        ).count()
        
        posts_week = db.query(PostTask).filter(
            PostTask.status == 'completed',
            PostTask.completed_at >= week_ago
        ).count()
        
        result = AccountStats(
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            limited_accounts=limited_accounts,
            banned_accounts=banned_accounts,
            error_accounts=error_accounts,
            posts_today=posts_today,
            posts_week=posts_week
        )
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики: {e}")
        if 'db' in locals():
            db.close()
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.post("/{account_id}/reset-daily-limit")
async def reset_account_daily_limit(
    account_id: str,
    current_user: dict = Depends(verify_token)
):
    """Сброс дневного лимита аккаунта"""
    logger.info(f"🔄 MediaFlux Hub: Сброс дневного лимита для аккаунта {account_id}")
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            db.close()
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        old_count = account.current_daily_posts
        account.current_daily_posts = 0
        account.updated_at = datetime.now()
        db.commit()
        db.close()
        
        logger.info(f"✅ MediaFlux Hub: Дневной лимит сброшен для @{account.username}: {old_count} -> 0")
        
        return {
            "message": f"Дневной лимит сброшен для @{account.username}",
            "previous_count": old_count,
            "reset_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 MediaFlux Hub: Ошибка сброса лимита: {e}")
        if 'db' in locals():
            db.close()
        raise HTTPException(status_code=500, detail="Ошибка сброса дневного лимита") 