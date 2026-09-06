# VKR_MAIN - Система управления театром

## Кратко о проекте

Проект состоит из двух частей:

- `api/` - FastAPI backend (ORM-модели, CRUD, auth, эндпоинты).
- `frontend/` + `backend/repositories/` - Qt-клиент (PySide6), который работает через HTTP API.

## Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте окружение: в корне проекта может использоваться файл `.env` (см. `api/config.py`, `app/config.py`). Для клиента важен **`API_BASE_URL`** (по умолчанию `http://localhost:8000`).

 Если база уже создана со старой схемой, для поля роли сотрудника может понадобиться:  
   `ALTER TABLE "Employee" ALTER COLUMN role TYPE VARCHAR(64);`  
   Подробнее о ролях и правах: [docs/SECURITY_ROLES.md](docs/SECURITY_ROLES.md).

 Для **файлов ТЗ сценариев** в таблице `Scenario` нужны колонки `tz_*` (см. `migrations/add_scenario_tz_columns.sql`). Применить к PostgreSQL можно так:  
   `python scripts/apply_scenario_tz_migration.py`  
   Опционально: `SCENARIO_TZ_UPLOAD_ROOT`, `N8N_TZ_WEBHOOK_URL`, `N8N_TZ_TIMEOUT_SEC` в `.env` (см. `api/config.py`, [docs/RUNNING.md](docs/RUNNING.md)).

3. Запустите API-сервер:
```bash
python start_api.py
```

4. Запустите основное приложение:
```bash
python start_app.py
```

Альтернативно, вы можете использовать скрипт для запуска обоих компонентов:
```bash
launch_app.bat
```

### Docker (PostgreSQL + API)

Поднять только БД и API в контейнерах:

```bash
docker compose up --build
```

API будет доступен на `http://localhost:8000`. Клиент на машине пользователя: в `.env` укажите `API_BASE_URL=http://localhost:8000` и запустите `python start_app.py`.

### Тесты

```bash
python -m pytest
```

### Документация

- [Руководство пользователя](docs/USER_GUIDE.md)
- [Запуск и окружение](docs/RUNNING.md)
- [Описание API](docs/API_DOCS.md)
- [Архитектура](docs/ARCHITECTURE.md)
- [Роли и безопасность](docs/SECURITY_ROLES.md)

### Логи клиента (Windows)

Файл: `%LOCALAPPDATA%\VKR_MAIN\logs\client.log`

## Структура проекта

- `start_api.py` - запуск API-сервера
- `start_app.py` - запуск основного приложения
- `launch_app.bat` - скрипт запуска
- `app/` - клиентская конфигурация и auth API-клиент
- `api/` - API-слой на базе FastAPI
- `backend/` - бэкенд-компоненты
  - `repositories/` - репозитории для работы с данными
- `frontend/` - фронтенд-компоненты
  - `views/` - представления
  - `ui/` - файлы интерфейса
- `docs/` - документация
- `docker-compose.yml`, `Dockerfile.api` - контейнеризация API и PostgreSQL
- `migrations/` - миграции базы данных
- `scripts/` - вспомогательные скрипты (например, применение миграции ТЗ)
- `data/scenario_tz/` - каталог загрузок ТЗ на сервере API (в git не коммитится, см. `.gitignore`)
- `tests/` - автотесты (pytest)