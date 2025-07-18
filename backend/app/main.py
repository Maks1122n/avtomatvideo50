# 🔥 RENDER FORCE UPDATE - 2024-12-19-22:10:00 - STATIC PATH HOTFIX  
# TIMESTAMP: 1734637200 - CRITICAL PATH FIX
# MediaFlux Hub - Instagram Automation Platform
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорт API модулей
try:
    from app.api import dashboard, accounts, content, tasks
    API_AVAILABLE = True
    logger.info("✅ All API modules imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import API modules: {e}")
    API_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle события приложения"""
    logger.info("🚀 MediaFlux Hub запускается...")
    if API_AVAILABLE:
        logger.info("✅ API endpoints активны")
    else:
        logger.warning("⚠️ API endpoints недоступны")
    yield
    logger.info("🛑 MediaFlux Hub останавливается...")

# Создание приложения
app = FastAPI(
    title="MediaFlux Hub",
    description="Instagram Reels Automation Platform", 
    version="1.0.0",
    lifespan=lifespan
)

# Шаблоны - ИСПРАВЛЕННЫЙ ПУТЬ
templates = Jinja2Templates(directory="../templates")

# Статические файлы - ИСПРАВЛЕННЫЙ ПУТЬ  
app.mount("/static", StaticFiles(directory="../static"), name="static")

# Подключение API роутеров ТОЛЬКО если доступны
if API_AVAILABLE:
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"]) 
    app.include_router(content.router, prefix="/api/content", tags=["Content"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
    logger.info("✅ All API routers connected")

# Главная страница - перенаправление на контент
@app.get("/", response_class=HTMLResponse)
async def dashboard_redirect():
    """Перенаправление на страницу контента как главную"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/content", status_code=302)

# Отдельный роут для красивого дашборда
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Страницы навигации
@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request):
    return templates.TemplateResponse("accounts.html", {"request": request})

@app.get("/content", response_class=HTMLResponse)
async def content_page(request: Request):
    return templates.TemplateResponse("content.html", {"request": request})

@app.get("/schedule", response_class=HTMLResponse)  
async def schedule_page(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

@app.get("/proxies", response_class=HTMLResponse)
async def proxies_page(request: Request):
    return templates.TemplateResponse("proxies.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# 🔍 ДИАГНОСТИЧЕСКАЯ ТЕСТОВАЯ СТРАНИЦА
@app.get("/test-buttons", response_class=HTMLResponse)
async def test_buttons_page(request: Request):
    return templates.TemplateResponse("test-buttons.html", {"request": request})

# Health check
@app.get("/health")
async def health_check():
    import datetime
    return {
        "status": "healthy",
        "service": "MediaFlux Hub",
        "version": "1.0.0",
        "api_available": API_AVAILABLE,
        "timestamp": datetime.datetime.now().isoformat(),
        "deployment_id": "TEST_BUTTONS_FORCE_UPDATE_001",
        "test_page_available": True
    }

# Favicon
@app.get("/favicon.ico")
async def favicon():
    """Favicon"""
    return {"message": "No favicon"} 