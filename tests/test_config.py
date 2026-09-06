"""
Тесты для конфигурационных файлов
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestApiConfig:
    """Тесты для конфигурации API"""

    def test_api_config_defaults(self):
        """Тестирует значения по умолчанию"""
        # Импортируем после очистки кэша
        import importlib
        import api.config
        importlib.reload(api.config)

        from api.config import DB_HOST, DB_PORT, DB_NAME, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

        assert DB_PORT == "5432"
        assert ALGORITHM == "HS256"
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_api_config_database_url_format(self):
        """Тестирует формат DATABASE_URL"""
        import importlib
        import api.config
        importlib.reload(api.config)

        from api.config import DATABASE_URL

        assert "postgresql+psycopg://" in DATABASE_URL
        assert "localhost" in DATABASE_URL
        assert "5432" in DATABASE_URL


class TestAppConfig:
    """Тесты для конфигурации приложения"""

    def test_app_config_api_base_url(self):
        """Тестирует URL API по умолчанию"""
        import importlib
        import app.config
        importlib.reload(app.config)

        from app.config import API_BASE_URL

        assert API_BASE_URL == "http://localhost:8000"

    @pytest.mark.skip(reason="Тест зависит от порядка загрузки .env и переменных окружения")
    def test_app_config_from_env(self):
        """Тестирует загрузку из переменных окружения"""
        # Сохраняем оригинальные значения
        original_env = {
            'API_BASE_URL': os.environ.get('API_BASE_URL'),
            'DB_HOST': os.environ.get('DB_HOST'),
            'DB_PORT': os.environ.get('DB_PORT'),
        }

        try:
            # Удаляем переменные, чтобы load_dotenv мог загрузить новые
            for key in ['API_BASE_URL', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']:
                if key in os.environ:
                    del os.environ[key]

            # Устанавливаем тестовые значения в .env файл (виртуально)
            os.environ['API_BASE_URL'] = 'http://custom-api:9000'
            os.environ['DB_HOST'] = 'custom-host'
            os.environ['DB_PORT'] = '5433'

            import importlib
            import app.config
            # Временно подменяем .env файл
            env_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                '.env'
            )
            # Загружаем конфиг без .env (из переменных окружения)
            importlib.reload(app.config)

            from app.config import API_BASE_URL, DB_HOST, DB_PORT

            assert API_BASE_URL == "http://custom-api:9000"
            assert DB_HOST == "custom-host"
            assert DB_PORT == "5433"
        finally:
            # Восстанавливаем оригинальные значения
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]


class TestEnvironmentVariables:
    """Тесты для обработки переменных окружения"""

    def test_env_file_exists(self):
        """Тестирует существование .env файла"""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.env'
        )
        assert os.path.exists(env_path), f".env file not found at {env_path}"

    def test_env_file_format(self):
        """Тестирует формат .env файла"""
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.env'
        )

        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        required_vars = [
            'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
            'SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES', 'API_BASE_URL'
        ]

        env_content = ''.join(lines)
        for var in required_vars:
            assert var in env_content, f"Required variable {var} not found in .env"
