#!/bin/bash

# MediaFlux Hub - Installation Script
# Instagram Reels Automation Platform

set -e

echo "🚀 Установка MediaFlux Hub - Instagram Reels Automation Platform..."
echo "=================================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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

# Проверка операционной системы
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/debian_version ]; then
            DISTRO="debian"
        elif [ -f /etc/redhat-release ]; then
            DISTRO="rhel"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Неподдерживаемая операционная система: $OSTYPE"
        exit 1
    fi
    log_info "Обнаружена ОС: $OS"
}

# Проверка Python версии
check_python() {
    log_info "Проверка Python..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            log_success "Python $PYTHON_VERSION найден"
            PYTHON_CMD="python3"
        else
            log_error "Требуется Python 3.11 или новее. Установлена версия: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 не найден. Установите Python 3.11 или новее."
        exit 1
    fi
}

# Установка системных зависимостей
install_system_deps() {
    log_info "Установка системных зависимостей..."
    
    case $OS in
        "linux")
            case $DISTRO in
                "debian")
                    sudo apt-get update
                    sudo apt-get install -y \
                        python3-pip \
                        python3-venv \
                        python3-dev \
                        build-essential \
                        libssl-dev \
                        libffi-dev \
                        libpq-dev \
                        curl \
                        wget \
                        unzip \
                        ffmpeg
                    ;;
                "rhel")
                    sudo yum update -y
                    sudo yum install -y \
                        python3-pip \
                        python3-devel \
                        gcc \
                        openssl-devel \
                        libffi-devel \
                        postgresql-devel \
                        curl \
                        wget \
                        unzip \
                        ffmpeg
                    ;;
            esac
            ;;
        "macos")
            if ! command -v brew &> /dev/null; then
                log_warning "Homebrew не найден. Установите Homebrew: https://brew.sh"
                exit 1
            fi
            brew install python@3.11 postgresql ffmpeg
            ;;
    esac
    
    log_success "Системные зависимости установлены"
}

# Создание виртуального окружения
create_venv() {
    log_info "Создание виртуального окружения..."
    
    if [ -d "venv" ]; then
        log_warning "Виртуальное окружение уже существует. Удаляем..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip setuptools wheel
    
    log_success "Виртуальное окружение создано"
}

# Установка Python зависимостей
install_python_deps() {
    log_info "Установка Python зависимостей..."
    
    source venv/bin/activate
    
    if [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt
        log_success "Python зависимости установлены"
    else
        log_error "Файл backend/requirements.txt не найден"
        exit 1
    fi
}

# Создание необходимых директорий
create_directories() {
    log_info "Создание необходимых директорий..."
    
    directories=(
        "content/motivation"
        "content/lifestyle" 
        "content/business"
        "content/entertainment"
        "logs"
        "proxies"
        "uploads"
        "backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Создана директория: $dir"
    done
    
    log_success "Директории созданы"
}

# Создание конфигурационных файлов
create_config_files() {
    log_info "Создание конфигурационных файлов..."
    
    # Копирование .env файла
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Файл .env создан из .env.example"
        else
            log_warning "Файл .env.example не найден. Создается базовый .env"
            cat > .env << EOF
# MediaFlux Hub Configuration
SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=sqlite:///./mediaflux_hub.db
CONTENT_PATH=./content
LOG_LEVEL=INFO
ENCRYPTION_KEY=$(openssl rand -base64 32 | head -c 32)
JWT_SECRET=$(openssl rand -base64 32)
EOF
        fi
    else
        log_info "Файл .env уже существует"
    fi
    
    # Создание примера прокси файла
    if [ ! -f "proxies/proxies.txt" ]; then
        cat > proxies/proxies.txt << EOF
# MediaFlux Hub - Proxy Configuration
# Формат: protocol://user:pass@ip:port|Country|City
# Пример:

# http://user1:pass1@123.456.789.1:8080|US|New York
# http://user2:pass2@123.456.789.2:8080|UK|London
# socks5://user3:pass3@123.456.789.3:1080|DE|Berlin

# Добавьте ваши прокси здесь:
EOF
        log_success "Создан пример файла прокси: proxies/proxies.txt"
    fi
    
    log_success "Конфигурационные файлы созданы"
}

# Инициализация базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    source venv/bin/activate
    
    cd backend
    
    # Создание миграций если их нет
    if [ ! -d "alembic/versions" ]; then
        log_info "Создание миграций Alembic..."
        alembic init alembic 2>/dev/null || true
        mkdir -p alembic/versions
    fi
    
    # Инициализация базы данных
    $PYTHON_CMD -c "from app.database import init_database; init_database()" || true
    
    cd ..
    
    log_success "База данных инициализирована"
}

# Проверка установки
verify_installation() {
    log_info "Проверка установки..."
    
    source venv/bin/activate
    
    # Проверка импорта основных модулей
    cd backend
    $PYTHON_CMD -c "
import sys
try:
    from app.main import app
    from app.database import SessionLocal
    from app.config import settings
    print('✅ Все модули импортированы успешно')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    sys.exit(1)
" || {
        log_error "Ошибка при проверке установки"
        exit 1
    }
    
    cd ..
    
    log_success "Установка прошла успешно!"
}

# Создание скрипта запуска
create_run_script() {
    log_info "Создание скрипта запуска..."
    
    cat > run.sh << 'EOF'
#!/bin/bash

# MediaFlux Hub - Run Script
echo "🚀 Запуск MediaFlux Hub - Instagram Reels Automation Platform..."

# Проверка .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден! Скопируйте .env.example в .env и настройте"
    exit 1
fi

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено! Запустите setup.sh"
    exit 1
fi

# Активация виртуального окружения
source venv/bin/activate

# Проверка папок с контентом
if [ ! -d "content" ]; then
    echo "❌ Папка content не найдена!"
    exit 1
fi

# Переход в backend директорию
cd backend

echo "🌐 MediaFlux Hub запуск веб-сервера на http://localhost:8000"
echo "📊 API документация: http://localhost:8000/api/docs"
echo "⚙️  Административный интерфейс: http://localhost:8000"
echo ""
echo "Демо аккаунты:"
echo "👨‍💼 Администратор: admin / mediaflux2024"
echo "👤 Пользователь: user / user123"
echo ""
echo "Нажмите Ctrl+C для остановки"
echo ""

# Запуск приложения
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ MediaFlux Hub остановлен"
EOF
    
    chmod +x run.sh
    log_success "Скрипт запуска создан: ./run.sh"
}

# Создание файла для Docker
create_docker_files() {
    log_info "Создание Docker файлов..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_warning "docker-compose.yml не найден, создается базовая версия"
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mediaflux-hub:
    build: 
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./content:/app/content
      - ./logs:/app/logs
      - ./proxies:/app/proxies
    env_file:
      - .env
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
EOF
    fi
    
    log_success "Docker файлы готовы"
}

# Финальная информация
show_final_info() {
    echo ""
    echo "=================================================================="
    log_success "🎉 Установка MediaFlux Hub завершена успешно!"
    echo "=================================================================="
    echo ""
    echo "📋 Следующие шаги:"
    echo ""
    echo "1. 📝 Отредактируйте файл .env:"
    echo "   nano .env"
    echo ""
    echo "2. 🌐 Добавьте прокси в файл:"
    echo "   nano proxies/proxies.txt"
    echo ""
    echo "3. 🎬 Добавьте видео в папки:"
    echo "   content/motivation/"
    echo "   content/lifestyle/"
    echo "   content/business/"
    echo "   content/entertainment/"
    echo ""
    echo "4. 🚀 Запустите MediaFlux Hub:"
    echo "   ./run.sh"
    echo ""
    echo "5. 🌐 Откройте в браузере:"
    echo "   http://localhost:8000"
    echo ""
    echo "=================================================================="
    log_info "💡 Полная документация: README.md"
    log_info "🆘 Поддержка: GitHub Issues"
    echo "=================================================================="
}

# Главная функция
main() {
    echo "MediaFlux Hub Installer v1.0.0"
    echo ""
    
    detect_os
    check_python
    install_system_deps
    create_venv
    install_python_deps
    create_directories
    create_config_files
    init_database
    create_run_script
    create_docker_files
    verify_installation
    show_final_info
}

# Обработка ошибок
trap 'log_error "Установка прервана"; exit 1' ERR

# Запуск установки
main "$@" 