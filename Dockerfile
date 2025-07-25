FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка зависимостей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir jinja2

# Копирование приложения
COPY backend/ ./

# Создание необходимых директорий
RUN mkdir -p content/motivation content/lifestyle content/business content/entertainment
RUN mkdir -p logs proxies uploads

# Копирование веб-интерфейса
COPY templates/ ./templates/
COPY static/ ./static/
COPY content/ ./content/

# Установка прав доступа
RUN chmod -R 755 .

# Переменная для порта (Render использует динамический PORT)
ENV PORT=8000
ENV ENVIRONMENT=production

# Экспорт порта
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Команда запуска для production
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 