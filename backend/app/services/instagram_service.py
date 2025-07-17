"""
MediaFlux Hub - Instagram API Service
Сервис для работы с Instagram Graph API с антибан-защитой
"""
import aiohttp
import asyncio
import logging
import random
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import json

from app.config import settings
from app.database import SessionLocal, Account
from app.services.proxy_service import ProxyManager

logger = logging.getLogger("mediaflux_hub.instagram")


class MediaFluxHubAPIService:
    """Сервис MediaFlux Hub для работы с Instagram Graph API"""
    
    def __init__(self):
        self.base_url = f"{settings.INSTAGRAM_BASE_URL}/{settings.INSTAGRAM_API_VERSION}"
        self.proxy_manager = ProxyManager()
        self.user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
    
    async def upload_reel(
        self, 
        account: Account, 
        video_url: str, 
        caption: str,
        share_to_feed: bool = True
    ) -> Tuple[bool, str]:
        """
        Полный процесс загрузки Reel в MediaFlux Hub:
        1. Создание контейнера
        2. Ожидание обработки
        3. Публикация
        """
        try:
            logger.info(f"📤 MediaFlux Hub: Начинаем загрузку Reel для @{account.username}")
            
            # Получаем прокси для аккаунта
            proxy = await self.proxy_manager.get_proxy_for_account(account.id)
            
            # Применяем антибан задержки
            await self._apply_antiban_delay()
            
            # Создаем контейнер
            container_id = await self._create_container(
                account, video_url, caption, share_to_feed, proxy
            )
            
            if not container_id:
                return False, "❌ Ошибка создания контейнера"
            
            logger.info(f"✅ MediaFlux Hub: Контейнер создан {container_id}")
            
            # Ожидаем обработки
            if not await self._wait_for_processing(container_id, account.access_token, proxy):
                return False, "⏰ Таймаут обработки видео"
            
            logger.info(f"✅ MediaFlux Hub: Видео обработано {container_id}")
            
            # Применяем задержку перед публикацией
            await asyncio.sleep(random.uniform(5, 15))
            
            # Публикуем
            media_id = await self._publish_container(container_id, account, proxy)
            
            if media_id:
                # Обновляем время последней публикации
                await self._update_account_last_post(account.id)
                
                logger.info(f"🎉 MediaFlux Hub: Reel успешно опубликован! ID: {media_id}")
                return True, media_id
            else:
                return False, "❌ Ошибка публикации"
                
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Критическая ошибка загрузки Reel для @{account.username}: {e}")
            
            # Обработка специфичных ошибок Instagram
            await self._handle_instagram_error(e, account.id)
            
            return False, str(e)
    
    async def _create_container(
        self, 
        account: Account, 
        video_url: str, 
        caption: str, 
        share_to_feed: bool,
        proxy: Optional[str]
    ) -> Optional[str]:
        """Создание контейнера для видео"""
        url = f"{self.base_url}/{account.instagram_account_id}/media"
        
        headers = self._get_headers(account.user_agent)
        
        data = {
            'access_token': account.access_token,
            'caption': caption,
            'media_type': 'REELS',
            'video_url': video_url,
            'share_to_feed': share_to_feed,
            'thumb_offset': random.randint(1000, 5000)  # Случайное превью
        }
        
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=settings.UPLOAD_TIMEOUT)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:
            
            kwargs = {'data': data}
            if proxy:
                kwargs['proxy'] = proxy
            
            try:
                async with session.post(url, **kwargs) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        return result.get('id')
                    else:
                        error_data = json.loads(response_text) if response_text else {}
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                        
                        logger.error(f"💥 MediaFlux Hub: Instagram API Error: {response.status} - {error_msg}")
                        
                        # Обработка rate limiting
                        if response.status == 429:
                            await self._handle_rate_limit(account.id)
                        
                        return None
                        
            except asyncio.TimeoutError:
                logger.error(f"⏰ MediaFlux Hub: Таймаут создания контейнера для @{account.username}")
                return None
            except Exception as e:
                logger.error(f"💥 MediaFlux Hub: Ошибка запроса создания контейнера: {e}")
                return None
    
    async def _wait_for_processing(
        self, 
        container_id: str, 
        access_token: str,
        proxy: Optional[str],
        max_wait: int = 300
    ) -> bool:
        """Ожидание обработки видео Instagram"""
        url = f"{self.base_url}/{container_id}"
        params = {
            'access_token': access_token,
            'fields': 'status_code'
        }
        
        start_time = asyncio.get_event_loop().time()
        check_interval = 10  # Проверяем каждые 10 секунд
        
        logger.info(f"⏳ MediaFlux Hub: Ожидание обработки контейнера {container_id}...")
        
        async with aiohttp.ClientSession() as session:
            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                kwargs = {'params': params}
                if proxy:
                    kwargs['proxy'] = proxy
                
                try:
                    async with session.get(url, **kwargs) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result.get('status_code')
                            
                            logger.debug(f"📊 MediaFlux Hub: Статус контейнера {container_id}: {status}")
                            
                            if status == 'FINISHED':
                                logger.info(f"✅ MediaFlux Hub: Контейнер {container_id} обработан!")
                                return True
                            elif status == 'ERROR':
                                logger.error(f"💥 MediaFlux Hub: Ошибка обработки контейнера {container_id}")
                                return False
                            elif status in ['IN_PROGRESS', 'PUBLISHED']:
                                # Продолжаем ждать
                                pass
                            
                        else:
                            logger.warning(f"⚠️ MediaFlux Hub: Ошибка проверки статуса: {response.status}")
                    
                    # Ждем перед следующей проверкой
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.warning(f"⚠️ MediaFlux Hub: Ошибка при проверке статуса: {e}")
                    await asyncio.sleep(check_interval)
        
        logger.error(f"⏰ MediaFlux Hub: Таймаут обработки контейнера {container_id}")
        return False
    
    async def _publish_container(
        self, 
        container_id: str, 
        account: Account,
        proxy: Optional[str]
    ) -> Optional[str]:
        """Публикация контейнера"""
        url = f"{self.base_url}/{account.instagram_account_id}/media_publish"
        
        headers = self._get_headers(account.user_agent)
        
        data = {
            'access_token': account.access_token,
            'creation_id': container_id
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            kwargs = {'data': data}
            if proxy:
                kwargs['proxy'] = proxy
            
            try:
                async with session.post(url, **kwargs) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        media_id = result.get('id')
                        
                        if media_id:
                            # Генерируем ссылку на пост
                            instagram_url = f"https://www.instagram.com/p/{media_id}/"
                            logger.info(f"🔗 MediaFlux Hub: Пост доступен по ссылке: {instagram_url}")
                        
                        return media_id
                    else:
                        error_data = json.loads(response_text) if response_text else {}
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                        logger.error(f"💥 MediaFlux Hub: Ошибка публикации: {response.status} - {error_msg}")
                        return None
                        
            except Exception as e:
                logger.error(f"💥 MediaFlux Hub: Ошибка запроса публикации: {e}")
                return None
    
    async def get_media_insights(
        self, 
        media_id: str, 
        account: Account,
        proxy: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Получение статистики поста"""
        url = f"{self.base_url}/{media_id}/insights"
        
        params = {
            'access_token': account.access_token,
            'metric': 'impressions,reach,likes,comments,shares,saves,profile_visits,follows'
        }
        
        headers = self._get_headers(account.user_agent)
        
        async with aiohttp.ClientSession(headers=headers) as session:
            kwargs = {'params': params}
            if proxy:
                kwargs['proxy'] = proxy
            
            try:
                async with session.get(url, **kwargs) as response:
                    if response.status == 200:
                        result = await response.json()
                        insights_data = {}
                        
                        for insight in result.get('data', []):
                            metric = insight.get('name')
                            values = insight.get('values', [])
                            if values:
                                insights_data[metric] = values[0].get('value', 0)
                        
                        return insights_data
                    else:
                        logger.warning(f"⚠️ MediaFlux Hub: Не удалось получить статистику: {response.status}")
                        return None
                        
            except Exception as e:
                logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики: {e}")
                return None
    
    def _get_headers(self, user_agent: Optional[str] = None) -> Dict[str, str]:
        """Генерация заголовков запроса"""
        headers = {
            'User-Agent': user_agent or random.choice(self.user_agents),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        return headers
    
    async def _apply_antiban_delay(self):
        """Применение антибан задержек"""
        # Случайная задержка между 2-8 секунд
        delay = random.uniform(2, 8)
        logger.debug(f"⏳ MediaFlux Hub: Антибан задержка {delay:.1f} секунд")
        await asyncio.sleep(delay)
    
    async def _handle_rate_limit(self, account_id: str):
        """Обработка rate limiting"""
        logger.warning(f"🚫 MediaFlux Hub: Rate limit для аккаунта {account_id}")
        
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                account.status = 'limited'
                account.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()
    
    async def _handle_instagram_error(self, error: Exception, account_id: str):
        """Обработка ошибок Instagram API"""
        error_str = str(error).lower()
        
        # Анализируем тип ошибки
        if 'rate limit' in error_str or '429' in error_str:
            await self._handle_rate_limit(account_id)
        elif 'permission' in error_str or '403' in error_str:
            await self._mark_account_error(account_id, 'permission_error')
        elif 'invalid token' in error_str or '401' in error_str:
            await self._mark_account_error(account_id, 'invalid_token')
    
    async def _mark_account_error(self, account_id: str, error_type: str):
        """Отметка аккаунта с ошибкой"""
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                account.status = 'error'
                account.updated_at = datetime.now()
                db.commit()
                
                logger.error(f"💥 MediaFlux Hub: Аккаунт {account.username} помечен как error: {error_type}")
        finally:
            db.close()
    
    async def _update_account_last_post(self, account_id: str):
        """Обновление времени последней публикации"""
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                account.last_post_time = datetime.now()
                account.last_activity = datetime.now()
                account.current_daily_posts += 1
                account.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()


class AntiBanManager:
    """MediaFlux Hub - Менеджер антибан-защиты"""
    
    # Временные ограничения
    MIN_DELAY_BETWEEN_POSTS = settings.MIN_DELAY_BETWEEN_POSTS  # 30 минут
    MAX_DELAY_BETWEEN_POSTS = settings.MAX_DELAY_BETWEEN_POSTS  # 2 часа
    
    # Дневные лимиты по типам аккаунтов
    DAILY_LIMITS = settings.DAILY_LIMITS
    
    @staticmethod
    async def can_post_now(account: Account) -> Tuple[bool, str]:
        """Проверка возможности публикации с учетом антибан-правил"""
        
        # Проверяем статус аккаунта
        if account.status != 'active':
            return False, f"Аккаунт имеет статус: {account.status}"
        
        # Проверяем дневной лимит
        if account.current_daily_posts >= account.daily_limit:
            return False, f"Достигнут дневной лимит ({account.daily_limit})"
        
        # Проверяем время последней публикации
        if account.last_post_time:
            time_diff = (datetime.now() - account.last_post_time).total_seconds()
            
            if time_diff < AntiBanManager.MIN_DELAY_BETWEEN_POSTS:
                wait_minutes = int((AntiBanManager.MIN_DELAY_BETWEEN_POSTS - time_diff) / 60)
                return False, f"Слишком рано. Ждите {wait_minutes} минут"
        
        return True, "OK"
    
    @staticmethod
    def randomize_posting_time(base_time: datetime) -> datetime:
        """Рандомизация времени публикации (±30 минут)"""
        offset_minutes = random.randint(-30, 30)
        return base_time + timedelta(minutes=offset_minutes)
    
    @staticmethod
    def get_account_type_limit(account_age_days: int) -> int:
        """Определение лимита аккаунта по возрасту"""
        if account_age_days < 30:
            return AntiBanManager.DAILY_LIMITS['new_account']
        elif account_age_days < 90:
            return AntiBanManager.DAILY_LIMITS['normal_account']
        elif account_age_days < 365:
            return AntiBanManager.DAILY_LIMITS['trusted_account']
        else:
            return AntiBanManager.DAILY_LIMITS['premium_account'] 