"""
Применяет migrations/add_scenario_tz_columns.sql к PostgreSQL из настроек api.config (тот же .env, что у API).

Запуск из корня проекта:
    python scripts/apply_scenario_tz_migration.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import create_engine, text

from api.config import DATABASE_URL


def main() -> None:
    sql_path = _ROOT / "migrations" / "add_scenario_tz_columns.sql"
    if not sql_path.is_file():
        raise SystemExit(f"Не найден файл миграции: {sql_path}")
    sql = sql_path.read_text(encoding="utf-8")
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("Миграция колонок ТЗ для Scenario применена успешно.")


if __name__ == "__main__":
    main()
