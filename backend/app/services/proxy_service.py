"""
MediaFlux Hub - Proxy Service
Сервис управления прокси-серверами с автоназначением и ротацией
"""
import logging
import random
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from app.config import settings
from app.database import SessionLocal, Proxy, Account

logger = logging.getLogger("mediaflux_hub.proxy")


class ProxyManager:
    """MediaFlux Hub - Менеджер прокси-серверов"""
    
    def __init__(self):
        self.proxy_file = settings.PROXIES_DIR / "proxies.txt"
        self.test_url = "https://httpbin.org/ip"
        self.timeout = 10
        self._proxy_cache = {}
        
    async def load_proxies_from_file(self) -> List[Dict[str, Any]]:
        """Загрузка прокси из файла"""
        proxies = []
        
        if not self.proxy_file.exists():
            logger.warning(f"📁 MediaFlux Hub: Файл прокси не найден: {self.proxy_file}")
            # Создаем пример файла
            await self._create_example_proxy_file()
            return proxies
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                proxy_data = self._parse_proxy_line(line)
                if proxy_data:
                    proxies.append(proxy_data)
                else:
                    logger.warning(f"⚠️ MediaFlux Hub: Некорректная строка прокси #{line_num}: {line}")
            
            logger.info(f"📊 MediaFlux Hub: Загружено {len(proxies)} прокси из файла")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка чтения файла прокси: {e}")
        
        return proxies
    
    def _parse_proxy_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Парсинг строки прокси"""
        try:
            # Формат: http://user:pass@ip:port|Country|City
            if '|' in line:
                proxy_url, location_info = line.split('|', 1)
                location_parts = location_info.split('|')
                country = location_parts[0] if len(location_parts) > 0 else "Unknown"
                city = location_parts[1] if len(location_parts) > 1 else "Unknown"
            else:
                proxy_url = line
                country = "Unknown"
                city = "Unknown"
            
            # Проверяем формат URL
            if not any(proxy_url.startswith(proto) for proto in ['http://', 'https://', 'socks4://', 'socks5://']):
                return None
            
            return {
                'proxy_url': proxy_url,
                'country': country,
                'city': city
            }
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка парсинга прокси: {e}")
            return None
    
    async def _create_example_proxy_file(self):
        """Создание примера файла прокси"""
        example_content = """# MediaFlux Hub - Proxy Configuration
# Формат: protocol://user:pass@ip:port|Country|City
# Пример:

# http://user1:pass1@123.456.789.1:8080|US|New York
# http://user2:pass2@123.456.789.2:8080|UK|London
# socks5://user3:pass3@123.456.789.3:1080|DE|Berlin

# Добавьте ваши прокси здесь:
"""
        
        try:
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                f.write(example_content)
            logger.info(f"📁 MediaFlux Hub: Создан пример файла прокси: {self.proxy_file}")
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка создания файла прокси: {e}")
    
    async def sync_proxies_to_database(self):
        """Синхронизация прокси с базой данных"""
        logger.info("🔄 MediaFlux Hub: Синхронизация прокси с базой данных...")
        
        file_proxies = await self.load_proxies_from_file()
        
        if not file_proxies:
            logger.warning("⚠️ MediaFlux Hub: Прокси не найдены в файле")
            return
        
        db = SessionLocal()
        try:
            # Получаем существующие прокси
            existing_proxies = {proxy.proxy_url: proxy for proxy in db.query(Proxy).all()}
            
            added_count = 0
            updated_count = 0
            
            for proxy_data in file_proxies:
                proxy_url = proxy_data['proxy_url']
                
                if proxy_url in existing_proxies:
                    # Обновляем существующий
                    proxy = existing_proxies[proxy_url]
                    proxy.country = proxy_data['country']
                    proxy.city = proxy_data['city']
                    proxy.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # Добавляем новый
                    proxy = Proxy(
                        proxy_url=proxy_url,
                        country=proxy_data['country'],
                        city=proxy_data['city']
                    )
                    db.add(proxy)
                    added_count += 1
            
            db.commit()
            logger.info(f"✅ MediaFlux Hub: Синхронизация завершена. Добавлено: {added_count}, Обновлено: {updated_count}")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка синхронизации прокси: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def test_proxy(self, proxy_url: str) -> bool:
        """Тестирование прокси"""
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                async with session.get(self.test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"✅ MediaFlux Hub: Прокси работает: {proxy_url} -> IP: {result.get('origin', 'unknown')}")
                        return True
                    else:
                        logger.warning(f"⚠️ MediaFlux Hub: Прокси вернул статус {response.status}: {proxy_url}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"⏰ MediaFlux Hub: Таймаут тестирования прокси: {proxy_url}")
            return False
        except Exception as e:
            logger.warning(f"💥 MediaFlux Hub: Ошибка тестирования прокси {proxy_url}: {e}")
            return False
    
    async def test_all_proxies(self) -> Dict[str, bool]:
        """Тестирование всех прокси"""
        logger.info("🧪 MediaFlux Hub: Начинаем тестирование всех прокси...")
        
        db = SessionLocal()
        try:
            proxies = db.query(Proxy).all()
            
            if not proxies:
                logger.warning("⚠️ MediaFlux Hub: Прокси не найдены в базе данных")
                return {}
            
            # Тестируем прокси параллельно (максимум 10 одновременно)
            semaphore = asyncio.Semaphore(10)
            tasks = []
            
            async def test_single_proxy(proxy):
                async with semaphore:
                    result = await self.test_proxy(proxy.proxy_url)
                    return proxy.proxy_url, result, proxy.id
            
            tasks = [test_single_proxy(proxy) for proxy in proxies]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обновляем статусы в базе данных
            test_results = {}
            working_count = 0
            
            for result in results:
                if isinstance(result, tuple):
                    proxy_url, is_working, proxy_id = result
                    test_results[proxy_url] = is_working
                    
                    # Обновляем статус в БД
                    proxy = db.query(Proxy).filter(Proxy.id == proxy_id).first()
                    if proxy:
                        if is_working:
                            proxy.is_active = True
                            proxy.error_count = 0
                            working_count += 1
                        else:
                            proxy.error_count += 1
                            if proxy.error_count >= proxy.max_errors:
                                proxy.is_active = False
                        
                        proxy.last_used = datetime.now()
                        proxy.updated_at = datetime.now()
            
            db.commit()
            
            logger.info(f"✅ MediaFlux Hub: Тестирование завершено. Работающих прокси: {working_count}/{len(proxies)}")
            return test_results
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка тестирования прокси: {e}")
            db.rollback()
            return {}
        finally:
            db.close()
    
    async def get_proxy_for_account(self, account_id: str) -> Optional[str]:
        """Получение прокси для аккаунта"""
        db = SessionLocal()
        try:
            # Проверяем, назначен ли уже прокси
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                return None
            
            if account.proxy_url:
                # Проверяем, что прокси еще активен
                proxy = db.query(Proxy).filter(Proxy.proxy_url == account.proxy_url).first()
                if proxy and proxy.is_active:
                    return account.proxy_url
            
            # Назначаем новый прокси
            new_proxy_url = await self.assign_proxy_to_account(account_id)
            return new_proxy_url
            
        finally:
            db.close()
    
    async def assign_proxy_to_account(self, account_id: str) -> Optional[str]:
        """Назначение прокси аккаунту"""
        db = SessionLocal()
        try:
            # Находим подходящий прокси
            available_proxies = db.query(Proxy).filter(
                Proxy.is_active == True,
                Proxy.accounts_assigned < Proxy.max_accounts
            ).order_by(Proxy.accounts_assigned.asc(), Proxy.last_used.asc()).all()
            
            if not available_proxies:
                logger.warning(f"⚠️ MediaFlux Hub: Нет доступных прокси для аккаунта {account_id}")
                return None
            
            # Выбираем случайный из топ-5 наименее загруженных
            top_proxies = available_proxies[:5]
            selected_proxy = random.choice(top_proxies)
            
            # Обновляем аккаунт
            account = db.query(Account).filter(Account.id == account_id).first()
            if account:
                # Освобождаем старый прокси
                if account.proxy_url:
                    await self._release_proxy_from_account(account.proxy_url, db)
                
                # Назначаем новый
                account.proxy_url = selected_proxy.proxy_url
                account.updated_at = datetime.now()
                
                # Обновляем счетчик прокси
                selected_proxy.accounts_assigned += 1
                selected_proxy.last_used = datetime.now()
                selected_proxy.updated_at = datetime.now()
                
                db.commit()
                
                logger.info(f"🔗 MediaFlux Hub: Прокси {selected_proxy.proxy_url} назначен аккаунту {account.username}")
                return selected_proxy.proxy_url
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка назначения прокси: {e}")
            db.rollback()
        finally:
            db.close()
        
        return None
    
    async def _release_proxy_from_account(self, proxy_url: str, db):
        """Освобождение прокси от аккаунта"""
        proxy = db.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
        if proxy and proxy.accounts_assigned > 0:
            proxy.accounts_assigned -= 1
            proxy.updated_at = datetime.now()
    
    async def rotate_proxy_on_error(self, account_id: str):
        """Смена прокси при ошибке"""
        logger.info(f"🔄 MediaFlux Hub: Ротация прокси для аккаунта {account_id}")
        
        db = SessionLocal()
        try:
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                return
            
            old_proxy_url = account.proxy_url
            
            # Помечаем старый прокси как проблемный
            if old_proxy_url:
                proxy = db.query(Proxy).filter(Proxy.proxy_url == old_proxy_url).first()
                if proxy:
                    proxy.error_count += 1
                    if proxy.error_count >= proxy.max_errors:
                        proxy.is_active = False
                        logger.warning(f"⚠️ MediaFlux Hub: Прокси {old_proxy_url} деактивирован из-за ошибок")
                    
                    proxy.accounts_assigned = max(0, proxy.accounts_assigned - 1)
                    proxy.updated_at = datetime.now()
            
            # Назначаем новый прокси
            account.proxy_url = None
            db.commit()
            
            new_proxy_url = await self.assign_proxy_to_account(account_id)
            
            if new_proxy_url:
                logger.info(f"✅ MediaFlux Hub: Прокси ротирован: {old_proxy_url} -> {new_proxy_url}")
            else:
                logger.error(f"💥 MediaFlux Hub: Не удалось назначить новый прокси для аккаунта {account_id}")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка ротации прокси: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def get_proxy_statistics(self) -> Dict[str, Any]:
        """Получение статистики прокси"""
        db = SessionLocal()
        try:
            total_proxies = db.query(Proxy).count()
            active_proxies = db.query(Proxy).filter(Proxy.is_active == True).count()
            assigned_proxies = db.query(Proxy).filter(Proxy.accounts_assigned > 0).count()
            
            # Распределение по странам
            country_stats = {}
            proxies = db.query(Proxy).all()
            for proxy in proxies:
                country = proxy.country or "Unknown"
                if country not in country_stats:
                    country_stats[country] = {'total': 0, 'active': 0}
                country_stats[country]['total'] += 1
                if proxy.is_active:
                    country_stats[country]['active'] += 1
            
            return {
                'total': total_proxies,
                'active': active_proxies,
                'assigned': assigned_proxies,
                'available': active_proxies - assigned_proxies,
                'countries': country_stats,
                'utilization': (assigned_proxies / max(active_proxies, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики прокси: {e}")
            return {}
        finally:
            db.close()
    
    async def optimize_proxy_assignment(self):
        """Оптимизация назначения прокси"""
        logger.info("🔧 MediaFlux Hub: Оптимизация назначения прокси...")
        
        db = SessionLocal()
        try:
            # Находим аккаунты с неактивными прокси
            accounts_needing_proxy = db.query(Account).join(
                Proxy, Account.proxy_url == Proxy.proxy_url, isouter=True
            ).filter(
                (Proxy.is_active == False) | (Proxy.id == None)
            ).all()
            
            reassigned_count = 0
            for account in accounts_needing_proxy:
                new_proxy = await self.assign_proxy_to_account(account.id)
                if new_proxy:
                    reassigned_count += 1
            
            logger.info(f"✅ MediaFlux Hub: Переназначено прокси для {reassigned_count} аккаунтов")
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка оптимизации прокси: {e}")
        finally:
            db.close() 