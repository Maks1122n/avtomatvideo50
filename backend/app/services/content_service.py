"""
MediaFlux Hub - Content Service
Сервис управления видео контентом с автоматической генерацией описаний
"""
import os
import random
import hashlib
import aiofiles
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from app.config import settings
from app.database import SessionLocal, ContentFolder, PostTask

logger = logging.getLogger("mediaflux_hub.content")


class MediaFluxContentService:
    """MediaFlux Hub - Сервис управления контентом"""
    
    def __init__(self):
        self.content_base_path = Path(settings.CONTENT_DIR)
        
        # Пулы хештегов по категориям
        self.hashtag_pools = {
            'motivation': [
                '#motivation', '#success', '#inspiration', '#mindset', 
                '#goals', '#hustle', '#grind', '#nevergiveup', '#believe',
                '#entrepreneur', '#businessmotivation', '#successmindset',
                '#motivationalquotes', '#dailymotivation', '#goalgetter',
                '#hardwork', '#determination', '#perseverance', '#ambition'
            ],
            'lifestyle': [
                '#lifestyle', '#daily', '#life', '#mood', '#vibes',
                '#aesthetic', '#selfcare', '#wellness', '#balance',
                '#dailylife', '#goodvibes', '#positive', '#happiness',
                '#mindfulness', '#peaceful', '#relaxing', '#cozy',
                '#inspiration', '#beautiful', '#simplicity'
            ],
            'business': [
                '#business', '#entrepreneur', '#startup', '#money',
                '#success', '#marketing', '#growth', '#leadership',
                '#businesstips', '#investing', '#wealth', '#finance',
                '#productivity', '#networking', '#innovation', '#strategy',
                '#businessowner', '#ceo', '#profitable', '#scaling'
            ],
            'entertainment': [
                '#entertainment', '#fun', '#viral', '#trending',
                '#funny', '#amazing', '#cool', '#awesome',
                '#wow', '#incredible', '#mindblowing', '#epic',
                '#satisfying', '#interesting', '#creative', '#unique',
                '#spectacular', '#fascinating', '#remarkable'
            ]
        }
        
        # Шаблоны описаний по категориям
        self.caption_templates = {
            'motivation': [
                "Каждый день - новая возможность стать лучше! 💪 {emojis}",
                "Успех начинается с первого шага! 🚀 {emojis}",
                "Твои мечты ждут действий! ✨ {emojis}",
                "Никогда не сдавайся! Твое время придет! 🔥 {emojis}",
                "Верь в себя и двигайся к цели! 🎯 {emojis}",
                "Сегодня отличный день для новых побед! 🏆 {emojis}",
                "Ты сильнее, чем думаешь! 💎 {emojis}",
                "Превращай препятствия в возможности! ⚡ {emojis}",
                "Будущее создается сегодня! 🌟 {emojis}",
                "Каждая попытка приближает к успеху! 🎪 {emojis}"
            ],
            'lifestyle': [
                "Наслаждайся каждым моментом жизни! 🌟 {emojis}",
                "Жизнь прекрасна в простых вещах! 💫 {emojis}",
                "Найди свой баланс и гармонию! ⚖️ {emojis}",
                "Будь собой - это твоя суперсила! 🌈 {emojis}",
                "Создавай моменты, которые запомнятся! 📸 {emojis}",
                "Позитивные вибрации каждый день! ✨ {emojis}",
                "Живи ярко и не оглядывайся! 🎨 {emojis}",
                "Счастье в мелочах! 🍃 {emojis}",
                "Твоя жизнь - твои правила! 🗝️ {emojis}",
                "Вдохновляйся и вдохновляй других! 🌻 {emojis}"
            ],
            'business': [
                "Строй свою бизнес-империю! 🏗️ {emojis}",
                "Успех требует действий, а не слов! 📈 {emojis}",
                "Инвестируй в себя - лучшая инвестиция! 💰 {emojis}",
                "Лидерство - это выбор, а не позиция! 👑 {emojis}",
                "Думай масштабно, действуй стратегически! 🎯 {emojis}",
                "Каждая неудача - урок для роста! 📚 {emojis}",
                "Создавай ценность и богатство придет! 💎 {emojis}",
                "Нетворкинг - ключ к новым возможностям! 🤝 {emojis}",
                "Инновации определяют будущее! 🚀 {emojis}",
                "Масштабируй бизнес правильно! ⚡ {emojis}"
            ],
            'entertainment': [
                "Это просто невероятно! 🤩 {emojis}",
                "Такое нужно обязательно увидеть! 👀 {emojis}",
                "Это поражает воображение! 🎉 {emojis}",
                "Топовый контент для вас! 🔥 {emojis}",
                "Не могу поверить своим глазам! 😱 {emojis}",
                "Это точно попадет в тренды! 📈 {emojis}",
                "Просто магия происходит! ✨ {emojis}",
                "Это заслуживает миллион лайков! ❤️ {emojis}",
                "Контент высшего качества! 💯 {emojis}",
                "Это изменит твой день к лучшему! 🌈 {emojis}"
            ]
        }
        
        # Эмодзи для добавления к описаниям
        self.emoji_sets = [
            ["🎯", "💎", "🌟"],
            ["⚡", "🎨", "🎪"],
            ["🔮", "🎲", "🎊"],
            ["🚀", "💫", "⭐"],
            ["🔥", "💪", "🏆"],
            ["✨", "🌈", "💫"],
            ["🎉", "🎭", "🎨"],
            ["💎", "⚡", "🔥"]
        ]
    
    async def scan_content_folders(self, db=None) -> List[ContentFolder]:
        """Сканирование папок с видео контентом"""
        logger.info("📁 MediaFlux Hub: Сканирование папок с контентом...")
        
        if db is None:
            db = SessionLocal()
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            folders = []
            
            # Проверяем существование базовой папки
            if not self.content_base_path.exists():
                logger.warning(f"📁 MediaFlux Hub: Папка контента не найдена: {self.content_base_path}")
                self.content_base_path.mkdir(parents=True, exist_ok=True)
                
                # Создаем категории
                for category in ['motivation', 'lifestyle', 'business', 'entertainment']:
                    (self.content_base_path / category).mkdir(exist_ok=True)
                
                logger.info("📁 MediaFlux Hub: Созданы папки для категорий контента")
                return folders
            
            # Сканируем каждую папку
            for folder_path in self.content_base_path.iterdir():
                if not folder_path.is_dir():
                    continue
                
                # Подсчитываем видео файлы
                video_files = self._get_video_files(folder_path)
                video_count = len(video_files)
                
                if video_count == 0:
                    logger.debug(f"📁 MediaFlux Hub: Папка {folder_path.name} пуста")
                    continue
                
                # Определяем категорию по названию папки
                category = self._determine_category(folder_path.name)
                
                # Проверяем, существует ли папка в БД
                existing_folder = db.query(ContentFolder).filter(
                    ContentFolder.path == str(folder_path)
                ).first()
                
                if existing_folder:
                    # Обновляем существующую
                    existing_folder.total_videos = video_count
                    existing_folder.category = category
                    existing_folder.updated_at = datetime.now()
                    folders.append(existing_folder)
                    logger.debug(f"📁 MediaFlux Hub: Обновлена папка {folder_path.name} ({video_count} видео)")
                else:
                    # Создаем новую
                    folder = ContentFolder(
                        name=folder_path.name,
                        path=str(folder_path),
                        total_videos=video_count,
                        category=category,
                        is_active=True
                    )
                    db.add(folder)
                    folders.append(folder)
                    logger.info(f"📁 MediaFlux Hub: Добавлена папка {folder_path.name} ({video_count} видео)")
            
            db.commit()
            logger.info(f"✅ MediaFlux Hub: Отсканировано {len(folders)} папок с контентом")
            
            return folders
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка сканирования контента: {e}")
            db.rollback()
            return []
        finally:
            if should_close_db:
                db.close()
    
    def _get_video_files(self, folder_path: Path) -> List[Path]:
        """Получение списка видео файлов в папке"""
        video_files = []
        
        for ext in settings.ALLOWED_VIDEO_EXTENSIONS:
            video_files.extend(folder_path.glob(f"*{ext}"))
            video_files.extend(folder_path.glob(f"*{ext.upper()}"))
        
        return video_files
    
    def _determine_category(self, folder_name: str) -> str:
        """Определение категории контента по названию папки"""
        folder_lower = folder_name.lower()
        
        motivation_keywords = ['motiv', 'success', 'inspire', 'goal', 'achieve']
        lifestyle_keywords = ['lifestyle', 'life', 'daily', 'routine', 'personal']
        business_keywords = ['business', 'money', 'entrepreneur', 'startup', 'finance']
        
        if any(keyword in folder_lower for keyword in motivation_keywords):
            return 'motivation'
        elif any(keyword in folder_lower for keyword in lifestyle_keywords):
            return 'lifestyle'
        elif any(keyword in folder_lower for keyword in business_keywords):
            return 'business'
        else:
            return 'entertainment'
    
    async def get_unused_video(self, folder_id: str, account_id: str, db) -> Optional[str]:
        """Получение неиспользованного видео для аккаунта"""
        try:
            # Получаем папку
            folder = db.query(ContentFolder).filter(
                ContentFolder.folder_id == folder_id
            ).first()
            
            if not folder:
                logger.warning(f"📁 MediaFlux Hub: Папка {folder_id} не найдена")
                return None
            
            # Получаем все видео файлы в папке
            folder_path = Path(folder.path)
            if not folder_path.exists():
                logger.warning(f"📁 MediaFlux Hub: Папка не существует: {folder_path}")
                return None
            
            video_files = self._get_video_files(folder_path)
            
            if not video_files:
                logger.warning(f"📁 MediaFlux Hub: Нет видео в папке {folder.name}")
                return None
            
            # Получаем уже использованные видео для этого аккаунта
            used_videos = set()
            used_tasks = db.query(PostTask).filter(
                PostTask.account_id == account_id,
                PostTask.folder_id == folder_id,
                PostTask.status.in_(['completed', 'processing'])
            ).all()
            
            for task in used_tasks:
                used_videos.add(str(task.video_path))
            
            # Находим неиспользованные видео
            available_videos = [
                str(video) for video in video_files 
                if str(video) not in used_videos
            ]
            
            if not available_videos:
                # Если все использованы, берем любое (начинаем новый цикл)
                available_videos = [str(video) for video in video_files]
                logger.info(f"🔄 MediaFlux Hub: Все видео использованы, начинаем новый цикл для папки {folder.name}")
            
            # Выбираем случайное видео
            selected_video = random.choice(available_videos)
            
            logger.debug(f"📽️ MediaFlux Hub: Выбрано видео: {Path(selected_video).name}")
            return selected_video
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения видео: {e}")
            return None
    
    async def generate_unique_caption(self, folder_name: str, video_path: str) -> str:
        """Генерация уникального описания для видео"""
        try:
            # Определяем категорию
            category = self._determine_category(folder_name)
            
            # Выбираем базовый шаблон
            templates = self.caption_templates.get(category, self.caption_templates['entertainment'])
            base_caption = random.choice(templates)
            
            # Выбираем случайные эмодзи
            emoji_set = random.choice(self.emoji_sets)
            emojis_str = ' '.join(emoji_set)
            
            # Подставляем эмодзи в шаблон
            caption = base_caption.format(emojis=emojis_str)
            
            # Генерируем хештеги
            hashtags = self._generate_hashtags(category)
            
            # Добавляем персонализацию на основе времени
            time_based_addition = self._get_time_based_addition()
            
            # Собираем финальное описание
            final_caption = f"{caption}\n\n{time_based_addition}\n\n{hashtags}"
            
            # Добавляем немного уникальности
            final_caption = self._add_uniqueness(final_caption, video_path)
            
            logger.debug(f"📝 MediaFlux Hub: Сгенерировано описание для {Path(video_path).name}")
            return final_caption
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка генерации описания: {e}")
            return "Потрясающий контент! 🔥\n\n#viral #trending #awesome"
    
    def _generate_hashtags(self, category: str) -> str:
        """Генерация релевантных хештегов"""
        category_hashtags = self.hashtag_pools.get(category, self.hashtag_pools['entertainment'])
        general_hashtags = ['#viral', '#trending', '#reels', '#explore', '#fyp', '#instagram', '#amazing']
        
        # Выбираем 4-6 хештегов из категории
        selected_category = random.sample(
            category_hashtags, 
            min(len(category_hashtags), random.randint(4, 6))
        )
        
        # Выбираем 2-4 общих хештега
        selected_general = random.sample(
            general_hashtags, 
            min(len(general_hashtags), random.randint(2, 4))
        )
        
        # Объединяем и перемешиваем
        all_hashtags = selected_category + selected_general
        random.shuffle(all_hashtags)
        
        # Ограничиваем до 10 хештегов максимум
        all_hashtags = all_hashtags[:10]
        
        return ' '.join(all_hashtags)
    
    def _get_time_based_addition(self) -> str:
        """Получение дополнения на основе времени"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            morning_phrases = [
                "Доброе утро! Начинаем день правильно! ☀️",
                "Утренняя мотивация для вас! 🌅",
                "Отличное начало дня! ⏰",
                "Утренний заряд энергии! ⚡"
            ]
            return random.choice(morning_phrases)
        elif 12 <= hour < 18:
            afternoon_phrases = [
                "Отличный день продолжается! 🌞",
                "Дневной заряд позитива! ⭐",
                "Продуктивного дня всем! 💪",
                "Дневная порция вдохновения! 🎯"
            ]
            return random.choice(afternoon_phrases)
        elif 18 <= hour < 22:
            evening_phrases = [
                "Вечерняя мотивация! 🌆",
                "Завершаем день на высокой ноте! 🎵",
                "Вечернее вдохновение! ✨",
                "Отличный вечер всем! 🌙"
            ]
            return random.choice(evening_phrases)
        else:
            night_phrases = [
                "Ночная мотивация для активных! 🌃",
                "Поздний контент для настоящих! 🦉",
                "Ночное вдохновение! 🌟",
                "Для тех, кто не спит! 😴"
            ]
            return random.choice(night_phrases)
    
    def _add_uniqueness(self, caption: str, video_path: str) -> str:
        """Добавление уникальности на основе видео"""
        # Получаем хеш файла для детерминированной уникальности
        file_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
        
        # На основе хеша выбираем дополнительные элементы
        hash_int = int(file_hash, 16)
        
        unique_additions = [
            "Этот момент бесценен! 💎",
            "Сохраняй и делись! 📌",
            "Твое мнение в комментариях! 💬",
            "Двойной тап, если согласен! ❤️",
            "Подписывайся на больше контента! 👆",
            "Отмечай друзей! 👥",
            "Какие эмоции вызывает? 🤔",
            "Что думаешь об этом? 💭"
        ]
        
        if hash_int % 3 == 0:  # Добавляем в 33% случаев
            addition = unique_additions[hash_int % len(unique_additions)]
            caption += f"\n\n{addition}"
        
        return caption
    
    async def upload_to_public_storage(self, video_path: str) -> Optional[str]:
        """Загрузка видео на публичное хранилище"""
        try:
            # Проверяем существование файла
            if not os.path.exists(video_path):
                logger.error(f"📽️ MediaFlux Hub: Видео файл не найден: {video_path}")
                return None
            
            # Получаем информацию о файле
            file_size = os.path.getsize(video_path)
            max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024  # Конвертируем в байты
            
            if file_size > max_size:
                logger.error(f"📽️ MediaFlux Hub: Файл слишком большой: {file_size} байт")
                return None
            
            # Генерируем уникальный хеш для файла
            with open(video_path, 'rb') as f:
                file_content = f.read()
                file_hash = hashlib.sha256(file_content).hexdigest()[:16]
            
            # В реальной реализации здесь должна быть загрузка на:
            # - AWS S3 с временными ссылками
            # - Google Cloud Storage  
            # - Cloudinary
            # - Или собственный CDN
            
            # Для демо генерируем временную ссылку
            file_extension = Path(video_path).suffix
            public_url = f"https://mediaflux-storage.example.com/videos/{file_hash}{file_extension}"
            
            logger.info(f"📤 MediaFlux Hub: Видео загружено: {Path(video_path).name} -> {public_url}")
            
            # В реальности здесь должна быть actual загрузка
            # Пока возвращаем временную ссылку
            return public_url
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка загрузки видео {video_path}: {e}")
            return None
    
    async def get_content_statistics(self, db=None) -> Dict[str, Any]:
        """Получение статистики контента"""
        if db is None:
            db = SessionLocal()
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            folders = db.query(ContentFolder).all()
            
            total_folders = len(folders)
            total_videos = sum(folder.total_videos for folder in folders)
            active_folders = sum(1 for folder in folders if folder.is_active)
            
            # Статистика по категориям
            categories_stats = {}
            for folder in folders:
                category = folder.category
                if category not in categories_stats:
                    categories_stats[category] = {
                        'folders': 0,
                        'videos': 0,
                        'used_videos': 0
                    }
                
                categories_stats[category]['folders'] += 1
                categories_stats[category]['videos'] += folder.total_videos
                categories_stats[category]['used_videos'] += folder.used_videos
            
            # Топ папки по количеству видео
            top_folders = sorted(
                [(f.name, f.total_videos, f.category) for f in folders],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'total_folders': total_folders,
                'active_folders': active_folders,
                'total_videos': total_videos,
                'categories': categories_stats,
                'top_folders': top_folders,
                'average_videos_per_folder': total_videos / max(total_folders, 1)
            }
            
        except Exception as e:
            logger.error(f"💥 MediaFlux Hub: Ошибка получения статистики контента: {e}")
            return {}
        finally:
            if should_close_db:
                db.close()
    
    async def validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """Валидация видео файла"""
        try:
            file_path_obj = Path(file_path)
            
            # Проверка существования
            if not file_path_obj.exists():
                return False, "Файл не существует"
            
            # Проверка расширения
            if file_path_obj.suffix.lower() not in settings.ALLOWED_VIDEO_EXTENSIONS:
                return False, f"Неподдерживаемый формат: {file_path_obj.suffix}"
            
            # Проверка размера
            file_size = file_path_obj.stat().st_size
            max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
            
            if file_size > max_size:
                return False, f"Файл слишком большой: {file_size / (1024*1024):.1f}MB"
            
            if file_size < 1024:  # Минимум 1KB
                return False, "Файл слишком маленький"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка валидации: {e}" 