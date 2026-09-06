# Инструкции по запуску API

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Настройка базы данных

1. Убедитесь, что PostgreSQL запущен
2. При необходимости измените настройки подключения в `api/config.py`
3. Запустите скрипт для создания структуры базы данных:

```bash
python -m api.setup_db
```

4. Если база уже существовала **до** добавления полей ТЗ для сценариев, один раз примените миграцию колонок:

```bash
python scripts/apply_scenario_tz_migration.py
```

(Или выполните SQL из `migrations/add_scenario_tz_columns.sql` вручную.)

## Запуск API

### Вариант 1: Через uvicorn напрямую

```bash
uvicorn api.api:app --reload --host 127.0.0.1 --port 8000
```

### Вариант 2: Через Python

```bash
python start_api.py
```

API будет доступен по адресу: http://localhost:8000

Документация к API будет доступна по адресу: http://localhost:8000/docs

## Переменные окружения

Для безопасной настройки приложения рекомендуется использовать переменные окружения.
Создайте файл `.env` в корне проекта.

**База и URL клиента** (см. `api/config.py`, `app/config.py`): `DB_*`, `API_BASE_URL`, `SECRET_KEY` и др.

**Файлы ТЗ сценариев:**

| Переменная | Назначение |
|------------|------------|
| `SCENARIO_TZ_UPLOAD_ROOT` | Каталог на сервере API для хранения загрузок (по умолчанию `data/scenario_tz` под корнем проекта). |
| `N8N_TZ_WEBHOOK_URL` | URL POST-вебхука n8n для `POST .../tz-spec/process`. Пусто — обработка отключена (ответ 400 с пояснением). |
| `N8N_TZ_TIMEOUT_SEC` | Таймаут HTTP к n8n в секундах (по умолчанию 120). |

## Тестирование API

После запуска API можно протестировать его работу:

```bash
pytest tests/test_api.py
```

## Запуск клиента

После запуска API запустите клиент:

```bash
python start_app.py
```