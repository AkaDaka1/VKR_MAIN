"""
Конфигурационный файл для безопасного хранения настроек
"""
import logging
import os
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)

# Загружаем переменные из .env файла
# Ищем .env в текущей директории и в родительской
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)  # override=True перезаписывает существующие переменные
    logger.info("Loaded .env from: %s", env_path)
else:
    logger.warning(".env not found at: %s", env_path)

# Конфигурация базы данных
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "d7k_8TJsdt")  # В продакшене обязательно измените!

# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# URL базы данных для SQLAlchemy
# Используем psycopg v3 для совместимости с Python 3.14
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Параметры API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Файлы ТЗ сценариев (каталог на сервере API)
_API_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_TZ_DIR = os.path.join(_API_ROOT_DIR, "data", "scenario_tz")
SCENARIO_TZ_UPLOAD_ROOT = os.getenv("SCENARIO_TZ_UPLOAD_ROOT", _DEFAULT_TZ_DIR)

# n8n: POST исходного файла; ответ — тело обработанного файла (или настройте workflow под свой контракт)
N8N_TZ_WEBHOOK_URL = os.getenv("N8N_TZ_WEBHOOK_URL", "").strip()
N8N_TZ_TIMEOUT_SEC = int(os.getenv("N8N_TZ_TIMEOUT_SEC", "120"))