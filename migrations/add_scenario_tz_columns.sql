-- Файлы ТЗ сценария (исходник + результат n8n) и статус пайплайна.
-- Выполнить на существующей БД PostgreSQL один раз.
--
-- Либо из корня проекта:  python scripts/apply_scenario_tz_migration.py
-- (берёт тот же DATABASE_URL / .env, что и API).
--
-- SQLAlchemy использует таблицу "Scenario" (в кавычках). Скрипт struct.sql
-- без кавычек создаёт scenario (нижний регистр). Обрабатываем оба варианта.

DO $$
BEGIN
  IF to_regclass('public."Scenario"') IS NOT NULL THEN
    ALTER TABLE "Scenario"
      ADD COLUMN IF NOT EXISTS tz_source_filename VARCHAR(500),
      ADD COLUMN IF NOT EXISTS tz_source_relpath TEXT,
      ADD COLUMN IF NOT EXISTS tz_result_filename VARCHAR(500),
      ADD COLUMN IF NOT EXISTS tz_result_relpath TEXT,
      ADD COLUMN IF NOT EXISTS tz_pipeline_status VARCHAR(50);
  ELSIF to_regclass('public.scenario') IS NOT NULL THEN
    ALTER TABLE scenario
      ADD COLUMN IF NOT EXISTS tz_source_filename VARCHAR(500),
      ADD COLUMN IF NOT EXISTS tz_source_relpath TEXT,
      ADD COLUMN IF NOT EXISTS tz_result_filename VARCHAR(500),
      ADD COLUMN IF NOT EXISTS tz_result_relpath TEXT,
      ADD COLUMN IF NOT EXISTS tz_pipeline_status VARCHAR(50);
  END IF;
END $$;
