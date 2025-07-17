# 🚀 MediaFlux Hub - Instagram Reels Automation Platform

**MediaFlux Hub** - это профессиональная платформа для автоматизации публикаций Instagram Reels с мощным ИИ-планировщиком, антибан-защитой и современным веб-интерфейсом.

![MediaFlux Hub Dashboard](https://img.shields.io/badge/MediaFlux%20Hub-v1.0.0-blue?style=for-the-badge&logo=instagram)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## ✨ Ключевые возможности

- 🤖 **ИИ-планировщик** - Автоматическое создание расписания публикаций
- 🛡️ **Антибан-защита** - Продвинутые алгоритмы защиты от блокировок Instagram
- 📱 **Адаптивный интерфейс** - Современный темный дизайн с полной адаптивностью
- 🌐 **Прокси-система** - Автоматическое управление и ротация прокси
- 📊 **Аналитика** - Детальная статистика по аккаунтам и публикациям
- ⚡ **Высокая производительность** - Поддержка до 50+ аккаунтов одновременно
- 🔒 **Безопасность** - AES-256 шифрование токенов и JWT аутентификация

## 🏗️ Архитектура

```
MediaFlux Hub/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Бизнес-логика
│   │   ├── models/         # SQLAlchemy модели
│   │   └── core/           # Ядро системы
│   └── requirements.txt
├── frontend/               # Vanilla JS frontend
│   ├── static/
│   │   ├── css/           # Стили (темная тема)
│   │   └── js/            # JavaScript модули
│   └── templates/         # HTML шаблоны
├── content/               # Папки для видео контента
│   ├── motivation/
│   ├── lifestyle/
│   ├── business/
│   └── entertainment/
├── docker-compose.yml     # Docker конфигурация
└── README.md              # Эта документация
```

## ⚡ Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/username/avtomatvideo50.git
cd avtomatvideo50
```

### 2. Автоматическая установка

```bash
# Linux/macOS
chmod +x setup.sh
./setup.sh

# Windows (PowerShell)
.\setup.ps1
```

### 3. Настройка конфигурации

```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем .env файл
nano .env
```

**Минимальная конфигурация:**
```env
SECRET_KEY=your-super-secret-key-here
ENCRYPTION_KEY=your-encryption-key-32-chars-long
JWT_SECRET=your-jwt-secret-key
DATABASE_URL=sqlite:///./mediaflux_hub.db
```

### 4. Запуск системы

```bash
# Простой запуск
./run.sh

# Или через Docker
docker-compose up -d
```

### 5. Открытие веб-интерфейса

Откройте [http://localhost:8000](http://localhost:8000) в браузере.

**Демо-аккаунты:**
- Администратор: `admin` / `mediaflux2024`
- Пользователь: `user` / `user123`

## 📋 Требования

### Системные требования

- **ОС:** Ubuntu 20.04+, CentOS 8+, Windows 10+, macOS 10.15+
- **Python:** 3.11 или новее
- **Память:** 4GB RAM (рекомендуется 8GB)
- **Дисковое пространство:** 20GB (100GB+ для большого объема контента)
- **Интернет:** Стабильное соединение 10+ Mbps

### Необходимые данные

#### Instagram Business аккаунты

Для каждого аккаунта подготовьте:
- ✅ Username Instagram
- ✅ Access Token (Instagram Graph API)
- ✅ Instagram Account ID
- ✅ Facebook Page ID

#### Прокси серверы

Минимум 17 прокси для 50 аккаунтов в формате:
```
http://user:pass@ip:port|Country|City
```

#### Видео контент

Структура папок:
```
content/
├── motivation/     (100+ MP4 файлов)
├── lifestyle/      (100+ MP4 файлов)  
├── business/       (100+ MP4 файлов)
└── entertainment/  (100+ MP4 файлов)
```

## 🔧 Настройка

### Добавление аккаунтов Instagram

1. Откройте dashboard MediaFlux Hub
2. Нажмите "Добавить аккаунт"
3. Заполните данные:
   - Username (без @)
   - Access Token
   - Instagram Account ID
   - Дневной лимит постов (1-20)

### Настройка прокси

1. Добавьте прокси в файл `proxies/proxies.txt`:
```
http://user1:pass1@123.456.789.1:8080|US|New York
http://user2:pass2@123.456.789.2:8080|UK|London
socks5://user3:pass3@123.456.789.3:1080|DE|Berlin
```

2. Выполните синхронизацию через веб-интерфейс

### Загрузка контента

1. Разместите MP4/MOV файлы в соответствующие папки:
   - `content/motivation/` - мотивационные видео
   - `content/lifestyle/` - лайфстайл контент
   - `content/business/` - бизнес контент
   - `content/entertainment/` - развлекательный контент

2. Запустите сканирование через интерфейс

## 🛡️ Безопасность и антибан

### Антибан алгоритмы

- **Временные ограничения:** 30 минут - 2 часа между постами
- **Дневные лимиты:** 2-12 постов в зависимости от типа аккаунта
- **Рандомизация:** Случайные интервалы и время публикации
- **Прокси ротация:** Автоматическая смена при ошибках
- **User-Agent ротация:** Имитация разных устройств

### Рекомендации

1. **Новые аккаунты:** Максимум 2 поста в день первые 30 дней
2. **Обычные аккаунты:** 3-5 постов в день
3. **Проверенные аккаунты:** До 8 постов в день
4. **Прокси качество:** Используйте только высококачественные прокси
5. **Контент качество:** Уникальные описания и хештеги

## 📊 Мониторинг и аналитика

### Dashboard функции

- 📈 **Статистика в реальном времени**
- 👥 **Управление аккаунтами**
- 📁 **Мониторинг контента**
- 🎯 **Настройки автоматизации**
- 📊 **Детальная аналитика**

### API endpoints

```
GET  /api/system/stats     # Системная статистика
GET  /api/accounts         # Список аккаунтов
POST /api/accounts         # Добавление аккаунта
GET  /api/content/folders  # Папки контента
GET  /api/tasks           # Задачи публикации
```

## 🚀 Deployment

### Production сервер

**Рекомендуемые характеристики:**
- 8+ CPU cores
- 16GB+ RAM
- 500GB+ SSD
- Ubuntu 20.04 LTS
- Статический IP

### Docker Compose (рекомендуется)

```bash
# Продакшен запуск
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# С мониторингом
docker-compose --profile monitoring up -d

# С бэкапами
docker-compose --profile backup up -d
```

### Настройка HTTPS

1. Получите SSL сертификат (Let's Encrypt)
2. Настройте Nginx reverse proxy
3. Обновите конфигурацию в `nginx/nginx.conf`

### Бэкапы

Автоматические бэкапы включают:
- База данных (PostgreSQL dump)
- Redis данные
- Контент файлы
- Конфигурация

## 🔍 Troubleshooting

### Частые проблемы

**1. Аккаунт заблокирован**
```bash
# Проверьте логи
docker-compose logs mediaflux-hub

# Измените прокси
# Уменьшите частоту постов
```

**2. Ошибка подключения к Instagram API**
```bash
# Проверьте токены
# Обновите Access Token
# Проверьте прокси
```

**3. Высокое использование ресурсов**
```bash
# Уменьшите количество одновременных задач
# Оптимизируйте размер видео файлов
# Добавьте больше RAM
```

### Логи и отладка

```bash
# Просмотр логов
tail -f logs/mediaflux_hub.log

# Docker логи
docker-compose logs -f

# Системные метрики
curl http://localhost:8000/api/system/stats
```

## 🤝 Поддержка

### Получение помощи

1. **Документация:** Полная документация в wiki репозитория
2. **Issues:** Создайте issue на GitHub для багов
3. **Discussions:** Обсуждения и вопросы в Discussions
4. **Email:** support@mediaflux-hub.com

### Участие в разработке

1. Fork репозитория
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

## 📝 Changelog

### v1.0.0 (2024-01-01)
- 🎉 Первый релиз MediaFlux Hub
- ✨ Автоматизация Instagram Reels
- 🎨 Темный адаптивный интерфейс
- 🛡️ Антибан-защита
- 🌐 Прокси-система
- 📊 Аналитика и мониторинг

## 📄 Лицензия

MIT License. См. [LICENSE](LICENSE) для деталей.

## ⚠️ Дисклеймер

MediaFlux Hub предназначен для легального использования в соответствии с условиями Instagram. Пользователи несут ответственность за соблюдение правил платформы и местного законодательства.

---

<div align="center">

**🚀 MediaFlux Hub - Автоматизируйте Instagram профессионально**

[![GitHub stars](https://img.shields.io/github/stars/username/avtomatvideo50?style=social)](https://github.com/username/avtomatvideo50)
[![GitHub forks](https://img.shields.io/github/forks/username/avtomatvideo50?style=social)](https://github.com/username/avtomatvideo50)

Made with ❤️ by MediaFlux Hub Team

</div> 