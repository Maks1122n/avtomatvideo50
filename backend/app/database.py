"""
MediaFlux Hub - Instagram Reels Automation Platform
Database Configuration and Models
"""
import logging
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from app.config import settings

# Настройка логирования
logger = logging.getLogger("mediaflux_hub.database")

# Создание engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False  # True для отладки SQL запросов
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

# Dependency для получения сессии базы данных
async def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Account(Base):
    """Модель аккаунта Instagram"""
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: f"acc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    username = Column(String, unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)  # Зашифрованный AES-256
    instagram_account_id = Column(String, nullable=False)
    proxy_url = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    daily_limit = Column(Integer, default=5)
    current_daily_posts = Column(Integer, default=0)
    status = Column(String, default='active')  # active, limited, banned, error
    last_post_time = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    post_tasks = relationship("PostTask", back_populates="account")


class Proxy(Base):
    """Модель прокси сервера"""
    __tablename__ = "proxies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy_url = Column(String, unique=True, nullable=False)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)
    max_errors = Column(Integer, default=3)
    last_used = Column(DateTime, nullable=True)
    accounts_assigned = Column(Integer, default=0)
    max_accounts = Column(Integer, default=3)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ContentFolder(Base):
    """Модель папки с контентом"""
    __tablename__ = "content_folders"
    
    folder_id = Column(String, primary_key=True, default=lambda: f"folder_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    total_videos = Column(Integer, default=0)
    used_videos = Column(Integer, default=0)
    posts_per_week = Column(Integer, default=7)
    category = Column(String, default='general')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    post_tasks = relationship("PostTask", back_populates="folder")


class PostTask(Base):
    """Модель задачи публикации"""
    __tablename__ = "post_tasks"
    
    task_id = Column(String, primary_key=True, default=lambda: f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)
    video_path = Column(String, nullable=False)
    original_caption = Column(Text, nullable=True)
    generated_caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    folder_id = Column(String, ForeignKey('content_folders.folder_id'), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default='pending')  # pending, processing, completed, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    media_id = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    account = relationship("Account", back_populates="post_tasks")
    folder = relationship("ContentFolder", back_populates="post_tasks")
    statistics = relationship("PostStatistics", back_populates="task", uselist=False)


class PostStatistics(Base):
    """Модель статистики постов"""
    __tablename__ = "post_statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey('post_tasks.task_id'), nullable=False)
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    profile_visits = Column(Integer, default=0)
    follows = Column(Integer, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    task = relationship("PostTask", back_populates="statistics")


class SystemLog(Base):
    """Модель системных логов"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String, nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    account_id = Column(String, nullable=True)
    task_id = Column(String, nullable=True)
    component = Column(String, nullable=True)  # scheduler, uploader, api, etc.
    details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=func.now())


class SystemSettings(Base):
    """Модель настроек системы"""
    __tablename__ = "system_settings"
    
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


def create_tables():
    """Создание всех таблиц"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ MediaFlux Hub: Таблицы базы данных созданы")
        
        # Создание дефолтных настроек
        db = SessionLocal()
        try:
            default_settings = [
                ("system_status", "active", "Статус системы MediaFlux Hub"),
                ("automation_enabled", "true", "Включена ли автоматизация"),
                ("daily_posts_limit", "250", "Лимит постов в день"),
                ("min_delay_between_posts", "1800", "Минимальная задержка между постами (сек)"),
                ("max_delay_between_posts", "7200", "Максимальная задержка между постами (сек)"),
                ("proxy_rotation_enabled", "true", "Включена ли ротация прокси"),
                ("content_scan_interval", "3600", "Интервал сканирования контента (сек)"),
                ("statistics_update_interval", "1800", "Интервал обновления статистики (сек)"),
            ]
            
            for key, value, description in default_settings:
                existing = db.query(SystemSettings).filter(SystemSettings.key == key).first()
                if not existing:
                    setting = SystemSettings(key=key, value=value, description=description)
                    db.add(setting)
            
            db.commit()
            logger.info("✅ MediaFlux Hub: Дефолтные настройки созданы")
            
        except Exception as e:
            logger.error(f"❌ MediaFlux Hub: Ошибка создания настроек: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ MediaFlux Hub: Ошибка создания таблиц: {e}")
        raise


def init_database():
    """Инициализация базы данных"""
    logger.info("🚀 MediaFlux Hub: Инициализация базы данных...")
    create_tables()
    logger.info("✅ MediaFlux Hub: База данных готова к работе!")


if __name__ == "__main__":
    init_database() 