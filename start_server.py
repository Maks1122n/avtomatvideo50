#!/usr/bin/env python3
"""
Скрипт запуска MediaFlux Hub сервера
"""
import os
import sys
import uvicorn

# Добавляем текущую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Запускаем сервер
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 