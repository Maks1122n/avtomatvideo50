"""
MediaFlux Hub - Instagram Reels Automation Platform
Configuration Settings
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки MediaFlux Hub"""
    
    # Основные настройки
    SECRET_KEY: str = "your-super-secret-key-here"
    DATABASE_URL: str = "sqlite:///./mediaflux_hub.db"
    CONTENT_PATH: str = "./content"
    LOG_LEVEL: str = "INFO"
    
    # Instagram API
    INSTAGRAM_API_VERSION: str = "v19.0"
    INSTAGRAM_BASE_URL: str = "https://graph.facebook.com"
    
    # Безопасность
    ENCRYPTION_KEY: str = "your-encryption-key-32-chars-long"
    JWT_SECRET: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Прокси
    DEFAULT_PROXY_PROVIDER: str = "brightdata"
    PROXY_ROTATION_ENABLED: bool = True
    MAX_ACCOUNTS_PER_PROXY: int = 3
    
    # Антибан настройки
    MIN_DELAY_BETWEEN_POSTS: int = 1800  # 30 минут
    MAX_DELAY_BETWEEN_POSTS: int = 7200  # 2 часа
    MAX_DAILY_POSTS_PER_ACCOUNT: int = 8
    
    # Система
    MAX_CONCURRENT_UPLOADS: int = 5
    UPLOAD_TIMEOUT: int = 300  # 5 минут
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 час
    
    # Уведомления (опционально)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    CONTENT_DIR: Path = BASE_DIR / "content"
    LOGS_DIR: Path = BASE_DIR / "logs"
    PROXIES_DIR: Path = BASE_DIR / "proxies"
    
    # Дневные лимиты по типам аккаунтов
    DAILY_LIMITS = {
        'new_account': 2,        # Новые аккаунты
        'normal_account': 5,     # Обычные аккаунты  
        'trusted_account': 8,    # Проверенные аккаунты
        'premium_account': 12    # Премиум аккаунты
    }
    
    # Типы видео файлов
    ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.mov']
    MAX_VIDEO_SIZE_MB = 500
    
    # Создание директорий
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Создаем необходимые директории
        self.CONTENT_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.PROXIES_DIR.mkdir(exist_ok=True)
        
        # Создаем папки для контента
        for category in ['motivation', 'lifestyle', 'business', 'entertainment']:
            (self.CONTENT_DIR / category).mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Экземпляр настроек
settings = Settings()

# Настройки логирования
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[{asctime}] {levelname} in {name}: {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} in {name} [{filename}:{lineno}]: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': settings.LOG_LEVEL,
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': settings.LOGS_DIR / 'mediaflux_hub.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {  # root logger
            'level': settings.LOG_LEVEL,
            'handlers': ['console', 'file'],
        },
        'mediaflux_hub': {
            'level': settings.LOG_LEVEL,
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
} 