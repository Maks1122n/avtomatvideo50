# MediaFlux Hub - Backend Dockerfile
# Multi-stage build для оптимизации размера образа

# Стадия 1: Базовый образ с зависимостями
FROM python:3.11-slim as base

# Метаданные
LABEL maintainer="MediaFlux Hub Team"
LABEL version="1.0.0"
LABEL description="MediaFlux Hub - Instagram Reels Automation Platform"

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    # Основные утилиты
    curl \
    wget \
    unzip \
    # Компиляторы и библиотеки для Python пакетов
    gcc \
    g++ \
    make \
    # Библиотеки для обработки изображений и видео
    libmagic1 \
    libmagic-dev \
    ffmpeg \
    # Библиотеки для криптографии
    libssl-dev \
    libffi-dev \
    # Библиотеки для PostgreSQL
    libpq-dev \
    # Утилиты для мониторинга
    htop \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создание пользователя для безопасности
RUN groupadd -r mediaflux && useradd -r -g mediaflux -s /bin/bash mediaflux

# Стадия 2: Установка Python зависимостей
FROM base as dependencies

# Установка pip и базовых инструментов
RUN pip install --upgrade pip setuptools wheel

# Копирование файлов зависимостей
COPY requirements.txt /tmp/requirements.txt

# Установка Python зависимостей
RUN pip install -r /tmp/requirements.txt

# Стадия 3: Финальный образ
FROM base as final

# Копирование установленных зависимостей
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Создание рабочей директории
WORKDIR /app

# Создание необходимых директорий
RUN mkdir -p \
    /app/logs \
    /app/content \
    /app/content/motivation \
    /app/content/lifestyle \
    /app/content/business \
    /app/content/entertainment \
    /app/proxies \
    /app/uploads \
    /app/backups

# Копирование приложения
COPY app/ /app/app/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

# Копирование статических файлов frontend
COPY ../frontend /app/frontend

# Создание файла инициализации базы данных
RUN echo "-- MediaFlux Hub Database Initialization" > /app/init.sql && \
    echo "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" >> /app/init.sql && \
    echo "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";" >> /app/init.sql

# Настройка прав доступа
RUN chown -R mediaflux:mediaflux /app && \
    chmod +x /app && \
    chmod -R 755 /app/logs \
    /app/content \
    /app/proxies \
    /app/uploads \
    /app/backups

# Создание примера конфигурации прокси
RUN echo "# MediaFlux Hub - Proxy Configuration" > /app/proxies/proxies.txt && \
    echo "# Формат: protocol://user:pass@ip:port|Country|City" >> /app/proxies/proxies.txt && \
    echo "# Пример:" >> /app/proxies/proxies.txt && \
    echo "# http://user1:pass1@123.456.789.1:8080|US|New York" >> /app/proxies/proxies.txt && \
    echo "# http://user2:pass2@123.456.789.2:8080|UK|London" >> /app/proxies/proxies.txt && \
    echo "" >> /app/proxies/proxies.txt && \
    echo "# Добавьте ваши прокси здесь:" >> /app/proxies/proxies.txt

# Создание скрипта запуска
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'echo "🚀 Starting MediaFlux Hub..."' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Ожидание готовности базы данных' >> /app/start.sh && \
    echo 'if [ "$DATABASE_URL" != "sqlite:///./mediaflux_hub.db" ]; then' >> /app/start.sh && \
    echo '  echo "⏳ Waiting for database..."' >> /app/start.sh && \
    echo '  python -c "' >> /app/start.sh && \
    echo 'import time' >> /app/start.sh && \
    echo 'import psycopg2' >> /app/start.sh && \
    echo 'import os' >> /app/start.sh && \
    echo 'import urllib.parse as urlparse' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo 'url = urlparse.urlparse(os.getenv(\"DATABASE_URL\"))' >> /app/start.sh && \
    echo 'for i in range(30):' >> /app/start.sh && \
    echo '    try:' >> /app/start.sh && \
    echo '        conn = psycopg2.connect(' >> /app/start.sh && \
    echo '            database=url.path[1:],' >> /app/start.sh && \
    echo '            user=url.username,' >> /app/start.sh && \
    echo '            password=url.password,' >> /app/start.sh && \
    echo '            host=url.hostname,' >> /app/start.sh && \
    echo '            port=url.port' >> /app/start.sh && \
    echo '        )' >> /app/start.sh && \
    echo '        conn.close()' >> /app/start.sh && \
    echo '        print(\"✅ Database connected!\")' >> /app/start.sh && \
    echo '        break' >> /app/start.sh && \
    echo '    except:' >> /app/start.sh && \
    echo '        print(f\"⏳ Waiting for database... ({i+1}/30)\")' >> /app/start.sh && \
    echo '        time.sleep(2)' >> /app/start.sh && \
    echo 'else:' >> /app/start.sh && \
    echo '    print(\"❌ Database connection failed!\")' >> /app/start.sh && \
    echo '    exit(1)' >> /app/start.sh && \
    echo '"' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Инициализация базы данных' >> /app/start.sh && \
    echo 'echo "📊 Initializing database..."' >> /app/start.sh && \
    echo 'python -c "from app.database import init_database; init_database()"' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Запуск приложения' >> /app/start.sh && \
    echo 'echo "🌐 Starting MediaFlux Hub on port 8000..."' >> /app/start.sh && \
    echo 'exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}' >> /app/start.sh && \
    chmod +x /app/start.sh

# Создание healthcheck скрипта
RUN echo '#!/bin/bash' > /app/healthcheck.sh && \
    echo 'curl -f http://localhost:8000/health || exit 1' >> /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Переключение на непривилегированного пользователя
USER mediaflux

# Переменные окружения для приложения
ENV PYTHONPATH=/app \
    APP_ENV=production \
    PORT=8000

# Экспорт порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Точка входа
ENTRYPOINT ["/app/start.sh"]

# Метаданные образа
LABEL org.opencontainers.image.title="MediaFlux Hub Backend"
LABEL org.opencontainers.image.description="Backend service for MediaFlux Hub - Instagram Reels Automation Platform"
LABEL org.opencontainers.image.url="https://github.com/mediaflux-hub/mediaflux-hub"
LABEL org.opencontainers.image.source="https://github.com/mediaflux-hub/mediaflux-hub"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2024-01-01T00:00:00Z"
LABEL org.opencontainers.image.licenses="MIT" 