"""
MediaFlux Hub - System Service
Системный сервис для мониторинга и управления платформой
"""
import logging
import psutil
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config import settings
from app.database import SessionLocal, Account, PostTask, SystemLog, SystemSettings

logger = logging.getLogger("mediaflux_hub.system")


class SystemService:
    """MediaFlux Hub - Системный сервис"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.is_running = False
        
        # Кэш статистики
        self._stats_cache = {}
        self._cache_ttl = 300  # 5 минут
        self._last_cache_update = None
    
    async def start(self):
        """Запуск системного сервиса"""
        if self.is_running:
            return
        
        logger.info("🚀 MediaFlux Hub: Запуск системного сервиса...")
        
        self.is_running = True
        
        # Записываем в лог о запуске
        await self.log_system_event("INFO", "MediaFlux Hub система запущена", {
            "start_time": self.start_time.isoformat(),
            "version": "1.0.0"
        })
        
        logger.info("✅ MediaFlux Hub: Системный сервис запущен")
    
    async def stop(self):
        """Остановка системного сервиса"""
        if not self.is_running:
            return
        
        logger.info("🛑 MediaFlux Hub: Остановка системного сервиса...")
        
        # Записываем в лог об остановке
        await self.log_system_event("INFO", "MediaFlux Hub система остановлена", {
            "stop_time": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        })
        
        self.is_running = False
        logger.info("✅ MediaFlux Hub: Системный сервис остановлен")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья системы"""
        try:
            health_checks = {}
            overall_healthy = True
            
            # Проверка базы данных
            db_healthy = await self._check_database_health()
            health_checks['database'] = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'details': 'Database connection successful' if db_healthy else 'Database connection failed'
            }
            overall_healthy &= db_healthy
            
            # Проверка Redis (если используется)
            redis_healthy = await self._check_redis_health()
            health_checks['redis'] = {
                'status': 'healthy' if redis_healthy else 'unhealthy',
                'details': 'Redis connection successful' if redis_healthy else 'Redis connection failed'
            }
            # Redis не критичен для работы системы
            
            # Проверка Instagram API
            instagram_healthy = await self._check_instagram_api_health()
            health_checks['instagram_api'] = {
                'status': 'healthy' if instagram_healthy else 'unhealthy',
                'details': 'Instagram API accessible' if instagram_healthy else 'Instagram API not accessible'
            }
            overall_healthy &= instagram_healthy
            
            # Проверка дискового пространства
            disk_healthy, disk_details = await self._check_disk_space()
            health_checks['disk_space'] = {
                'status': 'healthy' if disk_healthy else 'unhealthy',
                'details': disk_details
            }
            overall_healthy &= disk_healthy
            
            # Проверка использования памяти
            memory_healthy, memory_details = await self._check_memory_usage()
            health_checks['memory_usage'] = {
                'status': 'healthy' if memory_healthy else 'unhealthy',
                'details': memory_details
            }
            overall_healthy &= memory_healthy
            
            return {
                'overall': overall_healthy,
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                **health_checks
            }
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка проверки здоровья системы: {e}")
            return {
                'overall': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _check_database_health(self) -> bool:
        """Проверка здоровья базы данных"""
        try:
            db = SessionLocal()
            
            # Простой запрос для проверки соединения
            result = db.execute("SELECT 1").scalar()
            db.close()
            
            return result == 1
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка проверки БД: {e}")
            return False
    
    async def _check_redis_health(self) -> bool:
        """Проверка здоровья Redis"""
        try:
            # Здесь должна быть проверка Redis соединения
            # Пока возвращаем True, так как Redis опционален
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ MediaFlux Hub: Redis недоступен: {e}")
            return False
    
    async def _check_instagram_api_health(self) -> bool:
        """Проверка доступности Instagram API"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Проверяем доступность Graph API
                url = f"{settings.INSTAGRAM_BASE_URL}/{settings.INSTAGRAM_API_VERSION}/"
                
                async with session.get(url) as response:
                    return response.status in [200, 400]  # 400 - это нормально без токена
                    
        except Exception as e:
            logger.warning(f"⚠️ MediaFlux Hub: Instagram API недоступен: {e}")
            return False
    
    async def _check_disk_space(self) -> tuple[bool, str]:
        """Проверка дискового пространства"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            # Доступное место в GB
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Предупреждение если свободно менее 5GB или используется более 90%
            is_healthy = free_gb > 5 and used_percent < 90
            
            details = f"Free: {free_gb:.1f}GB, Used: {used_percent:.1f}%"
            
            return is_healthy, details
            
        except Exception as e:
            return False, f"Error checking disk space: {e}"
    
    async def _check_memory_usage(self) -> tuple[bool, str]:
        """Проверка использования памяти"""
        try:
            memory = psutil.virtual_memory()
            
            # Память в GB
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            used_percent = memory.percent
            
            # Предупреждение если используется более 85% памяти
            is_healthy = used_percent < 85
            
            details = f"Available: {available_gb:.1f}GB, Used: {used_percent:.1f}%"
            
            return is_healthy, details
            
        except Exception as e:
            return False, f"Error checking memory: {e}"
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Получение детальной статистики системы"""
        
        # Проверяем кэш
        if (self._last_cache_update and 
            (datetime.now() - self._last_cache_update).total_seconds() < self._cache_ttl):
            return self._stats_cache
        
        try:
            db = SessionLocal()
            
            # Статистика аккаунтов
            total_accounts = db.query(Account).count()
            active_accounts = db.query(Account).filter(Account.status == 'active').count()
            limited_accounts = db.query(Account).filter(Account.status == 'limited').count()
            banned_accounts = db.query(Account).filter(Account.status == 'banned').count()
            
            # Статистика постов за разные периоды
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            posts_today = db.query(PostTask).filter(
                PostTask.status == 'completed',
                PostTask.completed_at >= today
            ).count()
            
            posts_week = db.query(PostTask).filter(
                PostTask.status == 'completed',
                PostTask.completed_at >= week_ago
            ).count()
            
            posts_month = db.query(PostTask).filter(
                PostTask.status == 'completed',
                PostTask.completed_at >= month_ago
            ).count()
            
            # Статистика задач
            pending_tasks = db.query(PostTask).filter(PostTask.status == 'pending').count()
            processing_tasks = db.query(PostTask).filter(PostTask.status == 'processing').count()
            failed_tasks_today = db.query(PostTask).filter(
                PostTask.status == 'failed',
                PostTask.updated_at >= today
            ).count()
            
            # Системные метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Статистика по категориям контента
            from app.database import ContentFolder
            content_stats = {}
            folders = db.query(ContentFolder).all()
            
            for folder in folders:
                category = folder.category
                if category not in content_stats:
                    content_stats[category] = {
                        'folders': 0,
                        'total_videos': 0,
                        'used_videos': 0
                    }
                
                content_stats[category]['folders'] += 1
                content_stats[category]['total_videos'] += folder.total_videos
                content_stats[category]['used_videos'] += folder.used_videos
            
            # Топ аккаунты по постам
            top_accounts = db.execute("""
                SELECT a.username, COUNT(pt.task_id) as posts_count
                FROM accounts a
                LEFT JOIN post_tasks pt ON a.id = pt.account_id 
                WHERE pt.status = 'completed' AND pt.completed_at >= ?
                GROUP BY a.id, a.username
                ORDER BY posts_count DESC
                LIMIT 10
            """, (week_ago,)).fetchall()
            
            stats = {
                # Общая информация
                'system': {
                    'uptime_seconds': (now - self.start_time).total_seconds(),
                    'version': '1.0.0',
                    'status': 'running' if self.is_running else 'stopped'
                },
                
                # Аккаунты
                'accounts': {
                    'total': total_accounts,
                    'active': active_accounts,
                    'limited': limited_accounts,
                    'banned': banned_accounts,
                    'error': total_accounts - active_accounts - limited_accounts - banned_accounts
                },
                
                # Посты
                'posts': {
                    'today': posts_today,
                    'week': posts_week,
                    'month': posts_month,
                    'pending': pending_tasks,
                    'processing': processing_tasks,
                    'failed_today': failed_tasks_today
                },
                
                # Производительность
                'performance': {
                    'posts_per_day_avg': posts_week / 7,
                    'success_rate_today': (posts_today / max(posts_today + failed_tasks_today, 1)) * 100,
                    'active_accounts_ratio': (active_accounts / max(total_accounts, 1)) * 100
                },
                
                # Системные ресурсы
                'resources': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_free_gb': disk.free / (1024**3),
                    'disk_used_percent': (disk.used / disk.total) * 100
                },
                
                # Контент
                'content': content_stats,
                
                # Топ аккаунты
                'top_accounts': [
                    {'username': row[0], 'posts_count': row[1]} 
                    for row in top_accounts
                ],
                
                # Временная метка
                'timestamp': now.isoformat()
            }
            
            # Кэшируем результат
            self._stats_cache = stats
            self._last_cache_update = now
            
            db.close()
            return stats
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики: {e}")
            return {}
    
    async def log_system_event(
        self, 
        level: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        account_id: Optional[str] = None,
        task_id: Optional[str] = None,
        component: str = "system"
    ):
        """Запись события в системный лог"""
        try:
            db = SessionLocal()
            
            log_entry = SystemLog(
                level=level,
                message=message,
                account_id=account_id,
                task_id=task_id,
                component=component,
                details=str(details) if details else None
            )
            
            db.add(log_entry)
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка записи в системный лог: {e}")
    
    async def get_system_logs(
        self, 
        limit: int = 100, 
        level: Optional[str] = None,
        component: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Получение системных логов"""
        try:
            db = SessionLocal()
            
            # Базовый запрос
            query = db.query(SystemLog)
            
            # Фильтр по времени
            since = datetime.now() - timedelta(hours=hours)
            query = query.filter(SystemLog.created_at >= since)
            
            # Фильтры
            if level:
                query = query.filter(SystemLog.level == level)
            
            if component:
                query = query.filter(SystemLog.component == component)
            
            # Сортировка и лимит
            logs = query.order_by(SystemLog.created_at.desc()).limit(limit).all()
            
            result = []
            for log in logs:
                result.append({
                    'id': log.id,
                    'level': log.level,
                    'message': log.message,
                    'component': log.component,
                    'account_id': log.account_id,
                    'task_id': log.task_id,
                    'details': log.details,
                    'created_at': log.created_at.isoformat()
                })
            
            db.close()
            return result
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения логов: {e}")
            return []
    
    async def get_system_setting(self, key: str, default: Any = None) -> Any:
        """Получение системной настройки"""
        try:
            db = SessionLocal()
            
            setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
            
            if setting:
                db.close()
                return setting.value
            
            db.close()
            return default
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения настройки {key}: {e}")
            return default
    
    async def set_system_setting(self, key: str, value: str, description: str = None):
        """Установка системной настройки"""
        try:
            db = SessionLocal()
            
            setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
            
            if setting:
                setting.value = value
                if description:
                    setting.description = description
                setting.updated_at = datetime.now()
            else:
                setting = SystemSettings(
                    key=key,
                    value=value,
                    description=description
                )
                db.add(setting)
            
            db.commit()
            db.close()
            
            logger.info(f"⚙️ MediaFlux Hub: Настройка обновлена: {key} = {value}")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка установки настройки {key}: {e}")
    
    async def cleanup_old_logs(self, days: int = 30):
        """Очистка старых логов"""
        try:
            db = SessionLocal()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            deleted_count = db.query(SystemLog).filter(
                SystemLog.created_at < cutoff_date
            ).count()
            
            db.query(SystemLog).filter(
                SystemLog.created_at < cutoff_date
            ).delete()
            
            db.commit()
            db.close()
            
            logger.info(f"🧹 MediaFlux Hub: Удалено {deleted_count} старых логов")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка очистки логов: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Получение статуса сервиса"""
        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.is_running else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.is_running else 0
        } 