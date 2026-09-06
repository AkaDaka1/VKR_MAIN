"""
Файл запуска API-сервера
"""
import uvicorn
import sys
import os

# Добавляем корневую директорию в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Запускаем API-сервер
    uvicorn.run("api.api:app", host="127.0.0.1", port=8000, reload=True)