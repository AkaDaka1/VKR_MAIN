"""
Тесты для модуля аутентификации (app/auth_api.py)
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from app.auth_api import authenticate


class TestAuthentication:
    """Тесты для функции authenticate"""

    @patch('app.auth_api.requests.post')
    @patch('app.auth_api.requests.get')
    def test_authenticate_success(self, mock_get, mock_post):
        # Мокаем ответ для токена
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "bearer"
        }

        # Мокаем ответ для пользователя
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "id": 1,
            "username": "testuser",
            "role": "admin"
        }

        result = authenticate("testuser", "testpass")

        assert result is not None
        assert result['username'] == "testuser"
        assert result['role'] == "admin"
        assert result['id'] == 1

        # Проверяем, что запросы были сделаны правильно
        mock_post.assert_called_once_with(
            "http://localhost:8000/token",
            data={"username": "testuser", "password": "testpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=(5, 30),
        )
        mock_get.assert_called_once_with(
            "http://localhost:8000/users/me",
            headers={"Authorization": "Bearer test_token_123"},
            timeout=(5, 30),
        )

    @patch('app.auth_api.requests.post')
    def test_authenticate_wrong_password(self, mock_post):
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = "Incorrect username or password"

        result = authenticate("testuser", "wrongpass")

        assert result is None

    @patch('app.auth_api.requests.post')
    def test_authenticate_api_error(self, mock_post):
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"

        result = authenticate("testuser", "testpass")

        assert result is None

    @patch('app.auth_api.requests.post')
    def test_authenticate_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Connection refused")

        result = authenticate("testuser", "testpass")

        assert result is None

    @patch('app.auth_api.requests.post')
    @patch('app.auth_api.requests.get')
    def test_authenticate_user_info_error(self, mock_get, mock_post):
        # Токен получен, но информация о пользователе - нет
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "bearer"
        }

        mock_get.return_value.status_code = 401
        mock_get.return_value.text = "Unauthorized"

        result = authenticate("testuser", "testpass")

        assert result is None
