"""
MediaFlux Hub - Instagram Reels Automation Platform
Main FastAPI Application
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Импорт API роутеров
try:
    from app.api import dashboard, accounts, content, tasks
    API_AVAILABLE = True
except ImportError as e:
    logger.warning(f"API modules not available, running in limited mode: {e}")
    API_AVAILABLE = False

# Главная страница с веб-интерфейсом
@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Главная страница MediaFlux Hub Dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Страница управления аккаунтами"""
    return templates.TemplateResponse("accounts.html", {"request": request})

@app.get("/content", response_class=HTMLResponse)  
async def content_page(request: Request):
    """Страница управления контентом"""
    return templates.TemplateResponse("content.html", {"request": request})

@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request):
    """Страница планирования"""
    return templates.TemplateResponse("schedule.html", {"request": request})

# Подключение API роутеров
if API_AVAILABLE:
    # Подключаем все API роутеры
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
    app.include_router(content.router, prefix="/api/content", tags=["Content"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
    logger.info("✅ All API endpoints loaded successfully")
else:
    logger.warning("⚠️ Running without API endpoints")

# API endpoint для получения данных
@app.get("/api")
async def api_root():
    """API информация"""
    return {
        "message": "MediaFlux Hub API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "accounts": "/api/accounts", 
            "content": "/api/content",
            "tasks": "/api/tasks",
            "system": "/api/system",
            "proxies": "/api/proxies"
        } if API_AVAILABLE else "Limited mode - API not available"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 