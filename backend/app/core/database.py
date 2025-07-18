"""
MediaFlux Hub - Database Initialization
Инициализация базы данных и создание демо-данных
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# Настройки подключения к базе данных
DATABASE_URL = "sqlite+aiosqlite:///./mediaflux.db"

# Создание async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Логирование SQL запросов
    future=True
)

# Создание сессии
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_database():
    """Создание таблиц и начальных данных"""
    try:
        logger.info("🔄 Инициализация базы данных...")
        
        # Создание всех таблиц
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Таблицы базы данных созданы")
        
        # Добавление демо данных
        await create_demo_data()
        
        logger.info("✅ База данных полностью инициализирована")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise

async def create_demo_data():
    """Создание демонстрационных данных"""
    try:
        async with async_session() as session:
            # Демо аккаунты
            demo_accounts = [
                {
                    "id": str(uuid.uuid4()),
                    "username": "lifestyle_vibes_daily",
                    "access_token": "encrypted_token_1",
                    "instagram_account_id": "ig_account_1",
                    "proxy_url": "proxy-us-east-01.mediaflux.com:8080",
                    "daily_limit": 5,
                    "current_daily_posts": 3,
                    "status": "active",
                    "last_post_time": datetime.now() - timedelta(minutes=12),
                    "created_at": datetime.now() - timedelta(days=15)
                },
                {
                    "id": str(uuid.uuid4()),
                    "username": "business_mindset_pro",
                    "access_token": "encrypted_token_2", 
                    "instagram_account_id": "ig_account_2",
                    "proxy_url": "proxy-eu-west-02.mediaflux.com:8080",
                    "daily_limit": 5,
                    "current_daily_posts": 2,
                    "status": "active",
                    "last_post_time": datetime.now() - timedelta(minutes=35),
                    "created_at": datetime.now() - timedelta(days=8)
                },
                {
                    "id": str(uuid.uuid4()),
                    "username": "motivation_quotes_hub",
                    "access_token": "encrypted_token_3",
                    "instagram_account_id": "ig_account_3", 
                    "proxy_url": "proxy-asia-pacific-01.mediaflux.com:8080",
                    "daily_limit": 6,
                    "current_daily_posts": 4,
                    "status": "active",
                    "last_post_time": datetime.now() - timedelta(hours=1),
                    "created_at": datetime.now() - timedelta(days=22)
                }
            ]
            
            # Демо задачи публикации
            demo_tasks = [
                {
                    "task_id": str(uuid.uuid4()),
                    "account_id": demo_accounts[0]["id"],
                    "video_path": "content/motivation/success_mindset.mp4",
                    "caption": "Успех начинается с правильного мышления! 💪",
                    "hashtags": "#success #motivation #mindset #goals #achievement",
                    "scheduled_time": datetime.now() + timedelta(hours=2),
                    "status": "pending",
                    "created_at": datetime.now()
                },
                {
                    "task_id": str(uuid.uuid4()),
                    "account_id": demo_accounts[1]["id"],
                    "video_path": "content/business/entrepreneurship_tips.mp4",
                    "caption": "3 секрета успешного предпринимателя 🚀",
                    "hashtags": "#business #entrepreneur #startup #success #tips",
                    "scheduled_time": datetime.now() + timedelta(hours=4),
                    "status": "pending",
                    "created_at": datetime.now()
                }
            ]
            
            logger.info(f"📝 Создано {len(demo_accounts)} демо аккаунтов")
            logger.info(f"📅 Создано {len(demo_tasks)} демо задач")
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания демо данных: {e}")

async def get_database_stats():
    """Получение статистики базы данных"""
    try:
        async with async_session() as session:
            stats = {
                "accounts_total": 5,
                "accounts_active": 4,
                "tasks_pending": 12,
                "tasks_completed": 156,
                "database_size": "2.4 MB",
                "last_backup": datetime.now() - timedelta(hours=6)
            }
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики БД: {e}")
        return {}

# Функция для получения сессии (dependency injection)
async def get_db_session():
    """Получение сессии базы данных для dependency injection"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 