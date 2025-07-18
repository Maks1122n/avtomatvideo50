"""
MediaFlux Hub - Instagram Reels Automation Platform
Main FastAPI Application
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения"""
    logger.info("🚀 MediaFlux Hub запускается...")
    try:
        # Инициализация базы данных
        logger.info("✅ MediaFlux Hub успешно запущен")
        yield
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        raise
    finally:
        logger.info("🛑 MediaFlux Hub останавливается...")

# Создание FastAPI приложения
app = FastAPI(
    title="MediaFlux Hub",
    description="Instagram Reels Automation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check для Render
@app.get("/health")
async def health_check():
    """Health check endpoint для Render"""
    return {
        "status": "healthy",
        "service": "MediaFlux Hub",
        "version": "1.0.0"
    }

# Главная страница
@app.get("/")
async def read_root():
    """Главная страница"""
    return {
        "message": "MediaFlux Hub API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Статические файлы
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 