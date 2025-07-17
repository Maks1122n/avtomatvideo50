#!/bin/bash

# MediaFlux Hub - Run Script
# Instagram Reels Automation Platform

set -e

echo "🚀 Запуск MediaFlux Hub - Instagram Reels Automation Platform..."
echo "=================================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ASCII лого MediaFlux Hub
show_logo() {
    echo -e "${PURPLE}"
    cat << 'EOF'
    ███╗   ███╗███████╗██████╗ ██╗ █████╗ ███████╗██╗     ██╗   ██╗██╗  ██╗
    ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗██╔════╝██║     ██║   ██║╚██╗██╔╝
    ██╔████╔██║█████╗  ██║  ██║██║███████║█████╗  ██║     ██║   ██║ ╚███╔╝ 
    ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║██╔══╝  ██║     ██║   ██║ ██╔██╗ 
    ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║██║     ███████╗╚██████╔╝██╔╝ ██╗
    ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝
                                                                                
                        ██╗  ██╗██╗   ██╗██████╗ 
                        ██║  ██║██║   ██║██╔══██╗
                        ███████║██║   ██║██████╔╝
                        ██╔══██║██║   ██║██╔══██╗
                        ██║  ██║╚██████╔╝██████╔╝
                        ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
                                                  
         Instagram Reels Automation Platform v1.0.0
EOF
    echo -e "${NC}"
}

# Проверка .env файла
check_env_file() {
    log_info "Проверка конфигурации..."
    
    if [ ! -f .env ]; then
        log_error "Файл .env не найден!"
        echo ""
        echo "Решение:"
        echo "1. Скопируйте .env.example в .env:"
        echo "   cp .env.example .env"
        echo ""
        echo "2. Отредактируйте .env файл с вашими настройками"
        echo ""
        exit 1
    fi
    
    # Проверка обязательных переменных
    source .env
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-super-secret-key-here" ]; then
        log_warning "SECRET_KEY не настроен в .env файле"
        echo "Генерируем временный ключ..."
        export SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || date +%s | sha256sum | base64 | head -c 32)
    fi
    
    if [ -z "$ENCRYPTION_KEY" ] || [ "$ENCRYPTION_KEY" = "your-encryption-key-32-chars-long" ]; then
        log_warning "ENCRYPTION_KEY не настроен в .env файле"
        echo "Генерируем временный ключ..."
        export ENCRYPTION_KEY=$(openssl rand -base64 32 2>/dev/null | head -c 32 || date +%s | sha256sum | head -c 32)
    fi
    
    log_success "Конфигурация проверена"
}

# Проверка виртуального окружения
check_venv() {
    log_info "Проверка виртуального окружения..."
    
    if [ ! -d "venv" ]; then
        log_error "Виртуальное окружение не найдено!"
        echo ""
        echo "Решение:"
        echo "1. Запустите установку:"
        echo "   ./setup.sh"
        echo ""
        echo "2. Или создайте окружение вручную:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r backend/requirements.txt"
        echo ""
        exit 1
    fi
    
    log_success "Виртуальное окружение найдено"
}

# Проверка папок с контентом
check_content_folders() {
    log_info "Проверка папок с контентом..."
    
    if [ ! -d "content" ]; then
        log_error "Папка content не найдена!"
        echo ""
        echo "Создание папок..."
        mkdir -p content/{motivation,lifestyle,business,entertainment}
        log_success "Папки созданы"
    fi
    
    # Проверка наличия видео файлов
    video_count=0
    for dir in content/*/; do
        if [ -d "$dir" ]; then
            count=$(find "$dir" -name "*.mp4" -o -name "*.mov" | wc -l)
            video_count=$((video_count + count))
        fi
    done
    
    if [ $video_count -eq 0 ]; then
        log_warning "Видео файлы не найдены в папках content/"
        echo ""
        echo "Добавьте MP4/MOV файлы в папки:"
        echo "  content/motivation/    - мотивационные видео"
        echo "  content/lifestyle/     - лайфстайл контент"
        echo "  content/business/      - бизнес контент"
        echo "  content/entertainment/ - развлекательный контент"
        echo ""
    else
        log_success "Найдено $video_count видео файлов"
    fi
}

# Проверка системных зависимостей
check_system_deps() {
    log_info "Проверка системных зависимостей..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не найден. Установите Python 3.11 или новее"
        exit 1
    fi
    
    # Проверка uvicorn в виртуальном окружении
    source venv/bin/activate
    if ! python -c "import uvicorn" 2>/dev/null; then
        log_error "uvicorn не установлен. Запустите: pip install -r backend/requirements.txt"
        exit 1
    fi
    
    log_success "Системные зависимости проверены"
}

# Проверка доступности порта
check_port() {
    local port=${1:-8000}
    
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            log_warning "Порт $port уже используется"
            echo ""
            echo "Освободите порт или измените PORT в .env файле"
            echo ""
            echo "Для просмотра процесса: lsof -i :$port"
            echo "Для завершения: kill \$(lsof -t -i:$port)"
            echo ""
            read -p "Продолжить? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
}

# Инициализация базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    source venv/bin/activate
    cd backend
    
    # Инициализация с обработкой ошибок
    python -c "
try:
    from app.database import init_database
    init_database()
    print('✅ База данных инициализирована успешно')
except Exception as e:
    print(f'⚠️ Предупреждение при инициализации БД: {e}')
" 2>/dev/null || log_warning "База данных может быть не полностью инициализирована"
    
    cd ..
    log_success "База данных готова"
}

# Показ информации о запуске
show_startup_info() {
    echo ""
    echo "=================================================================="
    log_success "🎉 MediaFlux Hub готов к запуску!"
    echo "=================================================================="
    echo ""
    echo "📊 Веб-интерфейс:"
    echo "   🌐 http://localhost:8000"
    echo ""
    echo "📚 API документация:"
    echo "   📖 http://localhost:8000/api/docs"
    echo "   📋 http://localhost:8000/api/redoc"
    echo ""
    echo "👥 Демо аккаунты:"
    echo "   👨‍💼 Администратор: admin / mediaflux2024"
    echo "   👤 Пользователь: user / user123"
    echo ""
    echo "🔧 Системная информация:"
    echo "   🐍 Python: $(python3 --version)"
    echo "   📁 Рабочая директория: $(pwd)"
    echo "   🕒 Время запуска: $(date)"
    echo ""
    echo "=================================================================="
    echo "💡 Советы:"
    echo "   • Добавьте аккаунты Instagram через веб-интерфейс"
    echo "   • Настройте прокси в файле proxies/proxies.txt"
    echo "   • Загрузите видео в папки content/"
    echo "   • Нажмите Ctrl+C для остановки"
    echo "=================================================================="
    echo ""
}

# Обработчик сигналов для корректного завершения
cleanup() {
    echo ""
    echo ""
    log_info "🛑 Получен сигнал завершения..."
    log_info "📊 Статистика сессии:"
    
    if [ -f backend/logs/mediaflux_hub.log ]; then
        echo "   📈 Логи сохранены в: backend/logs/mediaflux_hub.log"
    fi
    
    log_success "✅ MediaFlux Hub остановлен корректно"
    echo ""
    echo "Спасибо за использование MediaFlux Hub! 🚀"
    exit 0
}

# Установка обработчиков сигналов
trap cleanup SIGINT SIGTERM

# Запуск приложения
start_application() {
    log_info "🚀 Запуск MediaFlux Hub сервера..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Переход в backend директорию
    cd backend
    
    # Запуск приложения с обработкой ошибок
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --reload \
        --reload-dir app \
        --log-level info \
        --access-log \
        --use-colors || {
        
        echo ""
        log_error "❌ Ошибка запуска MediaFlux Hub"
        echo ""
        echo "Возможные причины:"
        echo "1. Порт 8000 занят другим процессом"
        echo "2. Неправильная конфигурация в .env файле"
        echo "3. Отсутствуют зависимости Python"
        echo ""
        echo "Диагностика:"
        echo "• Проверьте логи: tail -f logs/mediaflux_hub.log"
        echo "• Проверьте порт: lsof -i :8000"
        echo "• Переустановите зависимости: pip install -r requirements.txt"
        echo ""
        exit 1
    }
}

# Основная функция
main() {
    show_logo
    
    # Предварительные проверки
    check_env_file
    check_venv
    check_system_deps
    check_content_folders
    check_port ${PORT:-8000}
    
    # Инициализация
    init_database
    
    # Информация о запуске
    show_startup_info
    
    # Запуск приложения
    start_application
}

# Обработка аргументов командной строки
case "${1:-}" in
    --help|-h)
        echo "MediaFlux Hub - Запуск платформы автоматизации Instagram"
        echo ""
        echo "Использование: $0 [опции]"
        echo ""
        echo "Опции:"
        echo "  --help, -h     Показать эту справку"
        echo "  --check        Только проверить конфигурацию"
        echo "  --port PORT    Использовать указанный порт"
        echo ""
        echo "Примеры:"
        echo "  $0              Обычный запуск"
        echo "  $0 --check     Проверка конфигурации"
        echo "  $0 --port 9000 Запуск на порту 9000"
        echo ""
        exit 0
        ;;
    --check)
        echo "🔍 Проверка конфигурации MediaFlux Hub..."
        check_env_file
        check_venv
        check_system_deps
        check_content_folders
        log_success "✅ Все проверки пройдены успешно!"
        exit 0
        ;;
    --port)
        if [ -n "$2" ]; then
            export PORT="$2"
            shift 2
        else
            log_error "Не указан номер порта"
            exit 1
        fi
        ;;
    *)
        # Обычный запуск
        ;;
esac

# Запуск основной функции
main "$@" 