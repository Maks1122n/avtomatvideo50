"""
MediaFlux Hub - Instagram Reels Automation Platform
Main FastAPI Application
Updated: 2024-12-19 for Render.com deployment
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определение путей в зависимости от окружения
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production":
    # Production пути (Render.com)
    TEMPLATES_DIR = "templates"
    STATIC_DIR = "static"
    logger.info("🌐 PRODUCTION MODE: Render.com deployment")
else:
    # Development пути (локальная разработка)
    TEMPLATES_DIR = "../templates"
    STATIC_DIR = "../static"
    logger.info("💻 DEVELOPMENT MODE: Local development")

logger.info(f"🌍 Environment: {ENVIRONMENT}")
logger.info(f"📁 Templates directory: {TEMPLATES_DIR}")
logger.info(f"🎨 Static directory: {STATIC_DIR}")

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

# Диагностический endpoint
@app.get("/debug")
async def debug_info():
    """Диагностический endpoint для проверки настроек"""
    import os
    import pathlib
    
    templates_exists = pathlib.Path(TEMPLATES_DIR).exists()
    static_exists = pathlib.Path(STATIC_DIR).exists()
    
    templates_files = []
    static_files = []
    
    if templates_exists:
        templates_files = [str(f) for f in pathlib.Path(TEMPLATES_DIR).glob("*")]
    
    if static_exists:
        static_files = [str(f) for f in pathlib.Path(STATIC_DIR).glob("**/*")]
    
    return {
        "environment": ENVIRONMENT,
        "templates_dir": TEMPLATES_DIR,
        "static_dir": STATIC_DIR,
        "templates_exists": templates_exists,
        "static_exists": static_exists,
        "templates_files": templates_files[:10],  # Первые 10 файлов
        "static_files": static_files[:20],        # Первые 20 файлов
        "working_directory": str(pathlib.Path.cwd()),
        "api_available": API_AVAILABLE,
        "python_path": os.environ.get("PYTHONPATH", "Not set")
    }

# Настройка шаблонов
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Статические файлы
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Детальное логирование статических файлов
import pathlib
templates_path = pathlib.Path(TEMPLATES_DIR)
static_path = pathlib.Path(STATIC_DIR)

logger.info(f"📁 Templates path exists: {templates_path.exists()}")
logger.info(f"🎨 Static path exists: {static_path.exists()}")

if templates_path.exists():
    template_files = list(templates_path.glob("*.html"))
    logger.info(f"📄 Found {len(template_files)} template files")
    
if static_path.exists():
    css_files = list(static_path.glob("**/*.css"))
    js_files = list(static_path.glob("**/*.js"))
    logger.info(f"🎨 Found {len(css_files)} CSS files, {len(js_files)} JS files")

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
        "environment": ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "accounts": "/api/accounts", 
            "content": "/api/content",
            "tasks": "/api/tasks"
        } if API_AVAILABLE else "Limited mode - API not available"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"🔄 Starting MediaFlux Hub at {datetime.now()}")
    uvicorn.run(app, host="0.0.0.0", port=8000) 