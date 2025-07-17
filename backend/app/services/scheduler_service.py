"""
MediaFlux Hub - Scheduler Service
Планировщик автоматических публикаций с антибан-защитой
"""
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.config import settings
from app.database import SessionLocal, Account, PostTask, ContentFolder
from app.services.instagram_service import MediaFluxHubAPIService, AntiBanManager
from app.services.content_service import MediaFluxContentService

logger = logging.getLogger("mediaflux_hub.scheduler")


class MediaFluxHubScheduler:
    """MediaFlux Hub - Планировщик публикаций"""
    
    def __init__(self):
        # Настройка APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        
        self.instagram_service = MediaFluxHubAPIService()
        self.content_service = MediaFluxContentService()
        self.antiban_manager = AntiBanManager()
        self.is_running = False
        
        # Статистика
        self.stats = {
            'posts_scheduled': 0,
            'posts_completed': 0,
            'posts_failed': 0,
            'last_schedule_generation': None,
            'active_tasks': 0
        }
    
    async def start(self):
        """Запуск планировщика MediaFlux Hub"""
        if self.is_running:
            logger.warning("⚠️ MediaFlux Hub: Планировщик уже запущен")
            return
        
        try:
            logger.info("🚀 MediaFlux Hub: Запуск планировщика...")
            
            # Генерация недельного расписания каждое воскресенье в 00:00
            self.scheduler.add_job(
                self.generate_weekly_schedule,
                CronTrigger(day_of_week=6, hour=0, minute=0),  # Воскресенье
                id="weekly_schedule_generation",
                replace_existing=True
            )
            
            # Обработка очереди публикаций каждые 2 минуты
            self.scheduler.add_job(
                self.process_posting_queue,
                'interval',
                minutes=2,
                id="posting_queue_processor",
                replace_existing=True
            )
            
            # Сброс дневных лимитов в полночь
            self.scheduler.add_job(
                self.reset_daily_limits,
                CronTrigger(hour=0, minute=1),
                id="daily_limits_reset",
                replace_existing=True
            )
            
            # Обновление статистики каждые 30 минут
            self.scheduler.add_job(
                self.update_post_statistics,
                'interval',
                minutes=30,
                id="statistics_updater",
                replace_existing=True
            )
            
            # Очистка старых логов каждые 24 часа
            self.scheduler.add_job(
                self.cleanup_old_data,
                CronTrigger(hour=2, minute=0),
                id="data_cleanup",
                replace_existing=True
            )
            
            # Сканирование контента каждые 6 часов
            self.scheduler.add_job(
                self.scan_content_folders,
                'interval',
                hours=6,
                id="content_scanner",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            # Генерируем начальное расписание
            await self.generate_weekly_schedule()
            
            logger.info("✅ MediaFlux Hub: Планировщик успешно запущен!")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка запуска планировщика: {e}")
            raise
    
    async def stop(self):
        """Остановка планировщика"""
        if not self.is_running:
            return
        
        logger.info("🛑 MediaFlux Hub: Остановка планировщика...")
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("✅ MediaFlux Hub: Планировщик остановлен")
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка остановки планировщика: {e}")
    
    async def generate_weekly_schedule(self):
        """Генерация расписания публикаций на неделю"""
        logger.info("📅 MediaFlux Hub: Генерация недельного расписания...")
        
        try:
            db = SessionLocal()
            
            # Получаем активные аккаунты
            accounts = db.query(Account).filter(Account.status == 'active').all()
            
            # Получаем активные папки с контентом
            folders = db.query(ContentFolder).filter(ContentFolder.is_active == True).all()
            
            if not accounts:
                logger.warning("⚠️ MediaFlux Hub: Нет активных аккаунтов для планирования")
                return
            
            if not folders:
                logger.warning("⚠️ MediaFlux Hub: Нет папок с контентом для планирования")
                return
            
            # Очищаем старые pending задачи
            db.query(PostTask).filter(PostTask.status == 'pending').delete()
            db.commit()
            
            total_tasks = 0
            
            # Планируем для каждого аккаунта
            for account in accounts:
                logger.info(f"📋 MediaFlux Hub: Планирование для @{account.username}")
                
                # Планируем на 7 дней вперед
                for day_offset in range(7):
                    target_date = datetime.now() + timedelta(days=day_offset)
                    
                    # Пропускаем прошедшие дни
                    if target_date.date() < datetime.now().date():
                        continue
                    
                    # Определяем количество постов на день
                    daily_posts = self._calculate_daily_posts(account, target_date)
                    
                    if daily_posts == 0:
                        continue
                    
                    # Создаем посты для этого дня
                    day_tasks = await self._create_daily_tasks(
                        account, target_date, daily_posts, folders, db
                    )
                    
                    total_tasks += len(day_tasks)
                    
                    logger.debug(f"📝 MediaFlux Hub: {len(day_tasks)} задач для @{account.username} на {target_date.strftime('%Y-%m-%d')}")
            
            db.commit()
            
            # Обновляем статистику
            self.stats['posts_scheduled'] = total_tasks
            self.stats['last_schedule_generation'] = datetime.now()
            
            logger.info(f"✅ MediaFlux Hub: Сгенерировано {total_tasks} задач на неделю")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка генерации расписания: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    def _calculate_daily_posts(self, account: Account, target_date: datetime) -> int:
        """Расчет количества постов в день для аккаунта"""
        
        # Базовое количество постов
        base_posts = min(account.daily_limit, settings.MAX_DAILY_POSTS_PER_ACCOUNT)
        
        # Корректировки по дням недели
        weekday = target_date.weekday()
        
        if weekday in [5, 6]:  # Выходные
            return max(1, int(base_posts * 0.7))  # Уменьшаем активность на выходных
        elif weekday in [0, 3]:  # Понедельник и четверг - более активные дни
            return min(account.daily_limit, int(base_posts * 1.2))
        else:
            return random.randint(max(1, base_posts - 1), base_posts)
    
    async def _create_daily_tasks(
        self, 
        account: Account, 
        target_date: datetime, 
        posts_count: int,
        folders: List[ContentFolder],
        db
    ) -> List[PostTask]:
        """Создание задач публикации на день"""
        
        tasks = []
        
        # Генерируем времена публикации
        posting_times = self._generate_posting_times(target_date, posts_count)
        
        for post_time in posting_times:
            # Выбираем случайную папку с контентом
            folder = random.choice(folders)
            
            # Получаем неиспользованное видео
            video_path = await self.content_service.get_unused_video(
                folder.folder_id, account.id, db
            )
            
            if not video_path:
                logger.warning(f"⚠️ MediaFlux Hub: Нет видео в папке {folder.name} для @{account.username}")
                continue
            
            # Генерируем уникальное описание
            caption = await self.content_service.generate_unique_caption(
                folder.name, video_path
            )
            
            # Создаем задачу
            task = PostTask(
                account_id=account.id,
                video_path=video_path,
                generated_caption=caption,
                folder_id=folder.folder_id,
                scheduled_time=post_time,
                status='pending'
            )
            
            db.add(task)
            tasks.append(task)
        
        return tasks
    
    def _generate_posting_times(self, target_date: datetime, posts_count: int) -> List[datetime]:
        """Генерация оптимальных времен публикации"""
        
        # Оптимальные временные окна для Instagram (по часам)
        optimal_hours = [
            (9, 11),    # Утро
            (13, 15),   # Обед  
            (17, 19),   # Вечер
            (20, 22)    # Ночь
        ]
        
        posting_times = []
        
        for i in range(posts_count):
            # Выбираем случайное временное окно
            start_hour, end_hour = random.choice(optimal_hours)
            
            # Генерируем случайное время в этом окне
            hour = random.randint(start_hour, end_hour - 1)
            minute = random.randint(0, 59)
            
            post_time = target_date.replace(
                hour=hour, 
                minute=minute, 
                second=random.randint(0, 59),
                microsecond=0
            )
            
            # Применяем антибан-рандомизацию
            post_time = self.antiban_manager.randomize_posting_time(post_time)
            
            # Проверяем, что время не в прошлом
            if post_time > datetime.now():
                posting_times.append(post_time)
        
        # Сортируем по времени
        posting_times.sort()
        
        # Обеспечиваем минимальные интервалы между постами
        adjusted_times = []
        last_time = None
        
        for post_time in posting_times:
            if last_time:
                time_diff = (post_time - last_time).total_seconds()
                if time_diff < settings.MIN_DELAY_BETWEEN_POSTS:
                    # Сдвигаем время
                    post_time = last_time + timedelta(seconds=settings.MIN_DELAY_BETWEEN_POSTS)
            
            adjusted_times.append(post_time)
            last_time = post_time
        
        return adjusted_times
    
    async def process_posting_queue(self):
        """Обработка очереди публикаций"""
        try:
            db = SessionLocal()
            
            # Получаем задачи готовые к выполнению
            current_time = datetime.now()
            ready_tasks = db.query(PostTask).filter(
                PostTask.status == 'pending',
                PostTask.scheduled_time <= current_time
            ).order_by(PostTask.scheduled_time.asc()).limit(10).all()
            
            if not ready_tasks:
                return
            
            logger.info(f"📤 MediaFlux Hub: Обработка {len(ready_tasks)} задач публикации...")
            
            # Обрабатываем задачи параллельно (максимум 3 одновременно)
            semaphore = asyncio.Semaphore(3)
            tasks = [
                self._process_single_task(task, semaphore) 
                for task in ready_tasks
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Подсчитываем результаты
            success_count = sum(1 for r in results if r is True)
            failed_count = len(results) - success_count
            
            self.stats['posts_completed'] += success_count
            self.stats['posts_failed'] += failed_count
            
            if success_count > 0:
                logger.info(f"✅ MediaFlux Hub: Успешно опубликовано {success_count} постов")
            
            if failed_count > 0:
                logger.warning(f"⚠️ MediaFlux Hub: Не удалось опубликовать {failed_count} постов")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка обработки очереди: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def _process_single_task(self, task: PostTask, semaphore: asyncio.Semaphore) -> bool:
        """Обработка одной задачи публикации"""
        async with semaphore:
            db = SessionLocal()
            try:
                # Получаем аккаунт
                account = db.query(Account).filter(Account.id == task.account_id).first()
                if not account:
                    await self._mark_task_failed(task.task_id, "Аккаунт не найден", db)
                    return False
                
                logger.info(f"📤 MediaFlux Hub: Публикация для @{account.username}")
                
                # Проверяем возможность публикации (антибан)
                can_post, reason = await self.antiban_manager.can_post_now(account)
                if not can_post:
                    # Откладываем задачу на 30 минут
                    new_time = datetime.now() + timedelta(minutes=30)
                    await self._reschedule_task(task.task_id, new_time, reason, db)
                    return False
                
                # Отмечаем задачу как обрабатываемую
                task.status = 'processing'
                task.attempts += 1
                task.updated_at = datetime.now()
                db.commit()
                
                # Загружаем видео на публичный хостинг
                video_url = await self.content_service.upload_to_public_storage(task.video_path)
                
                if not video_url:
                    await self._mark_task_failed(task.task_id, "Ошибка загрузки видео", db)
                    return False
                
                # Публикуем через Instagram API
                success, result = await self.instagram_service.upload_reel(
                    account=account,
                    video_url=video_url,
                    caption=task.generated_caption,
                    share_to_feed=True
                )
                
                if success:
                    # Успешная публикация
                    task.status = 'completed'
                    task.media_id = result
                    task.instagram_url = f"https://www.instagram.com/p/{result}/"
                    task.completed_at = datetime.now()
                    task.updated_at = datetime.now()
                    
                    # Обновляем счетчик аккаунта
                    account.current_daily_posts += 1
                    account.last_post_time = datetime.now()
                    account.last_activity = datetime.now()
                    account.updated_at = datetime.now()
                    
                    db.commit()
                    
                    logger.info(f"🎉 MediaFlux Hub: Reel опубликован! @{account.username} -> {result}")
                    return True
                else:
                    # Ошибка публикации
                    if task.attempts >= task.max_attempts:
                        await self._mark_task_failed(task.task_id, result, db)
                    else:
                        # Планируем повторную попытку через час
                        retry_time = datetime.now() + timedelta(hours=1)
                        await self._reschedule_task(task.task_id, retry_time, result, db)
                    
                    return False
                
            except Exception as e:
                logger.error(f"💥 MediaFlux Hub: Ошибка обработки задачи {task.task_id}: {e}")
                await self._mark_task_failed(task.task_id, str(e), db)
                return False
            finally:
                db.close()
    
    async def _mark_task_failed(self, task_id: str, error_message: str, db):
        """Отметка задачи как неудачной"""
        task = db.query(PostTask).filter(PostTask.task_id == task_id).first()
        if task:
            task.status = 'failed'
            task.error_message = error_message
            task.updated_at = datetime.now()
            db.commit()
    
    async def _reschedule_task(self, task_id: str, new_time: datetime, reason: str, db):
        """Перенос задачи на другое время"""
        task = db.query(PostTask).filter(PostTask.task_id == task_id).first()
        if task:
            task.scheduled_time = new_time
            task.status = 'pending'
            task.error_message = f"Перенесено: {reason}"
            task.updated_at = datetime.now()
            db.commit()
    
    async def reset_daily_limits(self):
        """Сброс дневных лимитов аккаунтов"""
        logger.info("🔄 MediaFlux Hub: Сброс дневных лимитов аккаунтов...")
        
        try:
            db = SessionLocal()
            
            # Сбрасываем счетчики постов
            accounts = db.query(Account).all()
            reset_count = 0
            
            for account in accounts:
                account.current_daily_posts = 0
                account.updated_at = datetime.now()
                reset_count += 1
            
            db.commit()
            
            logger.info(f"✅ MediaFlux Hub: Сброшены лимиты для {reset_count} аккаунтов")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка сброса лимитов: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    async def update_post_statistics(self):
        """Обновление статистики постов"""
        logger.info("📊 MediaFlux Hub: Обновление статистики постов...")
        
        try:
            db = SessionLocal()
            
            # Получаем опубликованные посты за последние 7 дней
            week_ago = datetime.now() - timedelta(days=7)
            completed_tasks = db.query(PostTask).filter(
                PostTask.status == 'completed',
                PostTask.completed_at >= week_ago,
                PostTask.media_id.isnot(None)
            ).all()
            
            updated_count = 0
            
            for task in completed_tasks:
                try:
                    account = db.query(Account).filter(Account.id == task.account_id).first()
                    if not account:
                        continue
                    
                    # Получаем статистику из Instagram API
                    insights = await self.instagram_service.get_media_insights(
                        task.media_id, account
                    )
                    
                    if insights:
                        # Обновляем статистику в базе данных
                        await self._update_task_statistics(task, insights, db)
                        updated_count += 1
                    
                    # Небольшая задержка между запросами
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"⚠️ MediaFlux Hub: Ошибка обновления статистики для {task.task_id}: {e}")
            
            logger.info(f"✅ MediaFlux Hub: Обновлена статистика для {updated_count} постов")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка обновления статистики: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def _update_task_statistics(self, task: PostTask, insights: Dict[str, Any], db):
        """Обновление статистики конкретной задачи"""
        from app.database import PostStatistics
        
        # Проверяем, есть ли уже запись статистики
        stats = db.query(PostStatistics).filter(PostStatistics.task_id == task.task_id).first()
        
        if not stats:
            stats = PostStatistics(task_id=task.task_id)
            db.add(stats)
        
        # Обновляем данные
        stats.impressions = insights.get('impressions', 0)
        stats.reach = insights.get('reach', 0)
        stats.likes = insights.get('likes', 0)
        stats.comments = insights.get('comments', 0)
        stats.shares = insights.get('shares', 0)
        stats.saves = insights.get('saves', 0)
        stats.profile_visits = insights.get('profile_visits', 0)
        stats.follows = insights.get('follows', 0)
        stats.updated_at = datetime.now()
        
        db.commit()
    
    async def cleanup_old_data(self):
        """Очистка старых данных"""
        logger.info("🧹 MediaFlux Hub: Очистка старых данных...")
        
        try:
            db = SessionLocal()
            
            # Удаляем старые логи (старше 30 дней)
            month_ago = datetime.now() - timedelta(days=30)
            from app.database import SystemLog
            
            old_logs_count = db.query(SystemLog).filter(
                SystemLog.created_at < month_ago
            ).count()
            
            db.query(SystemLog).filter(
                SystemLog.created_at < month_ago
            ).delete()
            
            # Удаляем неудачные задачи старше 7 дней
            week_ago = datetime.now() - timedelta(days=7)
            old_failed_tasks = db.query(PostTask).filter(
                PostTask.status == 'failed',
                PostTask.updated_at < week_ago
            ).count()
            
            db.query(PostTask).filter(
                PostTask.status == 'failed',
                PostTask.updated_at < week_ago
            ).delete()
            
            db.commit()
            
            logger.info(f"✅ MediaFlux Hub: Удалено {old_logs_count} старых логов и {old_failed_tasks} неудачных задач")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка очистки данных: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    async def scan_content_folders(self):
        """Сканирование папок с контентом"""
        logger.info("📁 MediaFlux Hub: Сканирование папок с контентом...")
        
        try:
            folders_scanned = await self.content_service.scan_content_folders()
            logger.info(f"✅ MediaFlux Hub: Отсканировано {len(folders_scanned)} папок")
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка сканирования контента: {e}")
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Получение статистики планировщика"""
        return {
            'is_running': self.is_running,
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.is_running else 0,
            **self.stats
        } 