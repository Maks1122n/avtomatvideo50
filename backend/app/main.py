"""
MediaFlux Hub - Instagram Reels Automation Platform
Main FastAPI Application
"""
import logging
import logging.config
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import time

from app.config import settings, LOGGING_CONFIG
from app.database import init_database
from app.api import accounts, content, tasks, system, proxies, auth
from app.services.scheduler_service import MediaFluxHubScheduler
from app.services.system_service import SystemService

# Настройка логирования
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("mediaflux_hub.main")

# Глобальный планировщик
scheduler = MediaFluxHubScheduler()
system_service = SystemService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 MediaFlux Hub: Запуск системы...")
    
    # Инициализация базы данных
    init_database()
    
    # Запуск планировщика
    await scheduler.start()
    
    # Запуск системного сервиса
    await system_service.start()
    
    logger.info("✅ MediaFlux Hub: Система полностью запущена!")
    
    yield
    
    # Остановка при завершении
    logger.info("🛑 MediaFlux Hub: Остановка системы...")
    await scheduler.stop()
    await system_service.stop()
    logger.info("✅ MediaFlux Hub: Система остановлена")


# Создание FastAPI приложения
app = FastAPI(
    title="MediaFlux Hub",
    description="Instagram Reels Automation Platform - Автоматизация публикаций Instagram Reels",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"MediaFlux Hub API: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    return response

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

# API роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(proxies.router, prefix="/api/proxies", tags=["Proxies"])

# Главная страница - Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница MediaFlux Hub Dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Страница аккаунтов
@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """Страница управления аккаунтами"""
    return templates.TemplateResponse("accounts.html", {"request": request})

# Страница контента
@app.get("/content", response_class=HTMLResponse)
async def content_page(request: Request):
    """Страница управления контентом"""
    return templates.TemplateResponse("content.html", {"request": request})

# Страница аналитики
@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Страница аналитики"""
    return templates.TemplateResponse("analytics.html", {"request": request})

# Страница настроек
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Страница настроек"""
    return templates.TemplateResponse("settings.html", {"request": request})

# Health check
@app.get("/health")
async def health_check():
    """Проверка состояния MediaFlux Hub"""
    try:
        health_status = await system_service.get_health_status()
        return {
            "status": "healthy" if health_status["overall"] else "unhealthy",
            "service": "MediaFlux Hub",
            "version": "1.0.0",
            "checks": health_status
        }
    except Exception as e:
        logger.error(f"MediaFlux Hub: Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Обработчик ошибок 404
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Обработчик 404 ошибок"""
    return templates.TemplateResponse(
        "404.html", 
        {"request": request}, 
        status_code=404
    )

# Обработчик ошибок 500
@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Обработчик 500 ошибок"""
    logger.error(f"MediaFlux Hub: Server error: {exc}")
    return templates.TemplateResponse(
        "500.html", 
        {"request": request}, 
        status_code=500
    )

if __name__ == "__main__":
    logger.info("🚀 MediaFlux Hub: Запуск через uvicorn...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    ) 