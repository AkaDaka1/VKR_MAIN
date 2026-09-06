"""
Тесты для репозиториев (backend/repositories)
Тестирует функции репозиториев через mocking API запросов
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from app.config import API_BASE_URL
from backend.repositories.employee_repo import (
    get_all_employees,
    add_employee,
    delete_employee_by_login,
    update_last_online,
)
from backend.repositories.franchise_repo import get_all_franchises, add_franchise


class TestEmployeeRepository:
    """Тесты для репозитория сотрудников"""

    @patch("backend.repositories.employee_repo.api_get")
    def test_get_all_employees_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "username": "user1", "role": "admin"},
            {"id": 2, "username": "user2", "role": "user"},
        ]
        mock_get.return_value = mock_response

        result = get_all_employees()

        assert len(result) == 2
        assert result[0]["username"] == "user1"
        mock_get.assert_called_once_with(API_BASE_URL, "/employees/")

    @patch("backend.repositories.employee_repo.api_get")
    def test_get_all_employees_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = get_all_employees()

        assert result == []

    @patch("backend.repositories.employee_repo.api_get")
    def test_get_all_employees_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = get_all_employees()

        assert result == []

    @patch("backend.repositories.employee_repo.api_post")
    def test_add_employee_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = add_employee("testuser", "testpass", "admin")

        assert result is True
        mock_post.assert_called_once()

    @patch("backend.repositories.employee_repo.api_post")
    def test_add_employee_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = add_employee("testuser", "testpass", "admin")

        assert result is False

    @patch("backend.repositories.employee_repo.api_get")
    @patch("backend.repositories.employee_repo.api_delete")
    def test_delete_employee_success(self, mock_delete, mock_get):
        mock_get.return_value.json.return_value = [{"id": 1, "username": "testuser", "role": "admin"}]
        mock_get.return_value.status_code = 200
        mock_delete.return_value.status_code = 200

        result = delete_employee_by_login("testuser")

        assert result is True
        mock_delete.assert_called_once_with(API_BASE_URL, "/employees/1")

    @patch("backend.repositories.employee_repo.api_get")
    def test_delete_employee_not_found(self, mock_get):
        mock_get.return_value.json.return_value = []
        mock_get.return_value.status_code = 200

        result = delete_employee_by_login("nonexistent")

        assert result is False

    def test_update_last_online(self):
        result = update_last_online("testuser")
        assert result is True


class TestFranchiseRepository:
    """Тесты для репозитория франшиз"""

    @patch("backend.repositories.franchise_repo.api_get")
    def test_get_all_franchises_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"contract_id": 1, "organization": "Franchise1"},
            {"contract_id": 2, "organization": "Franchise2"},
        ]
        mock_get.return_value = mock_response

        result = get_all_franchises()

        assert len(result) == 2
        assert result[0]["organization"] == "Franchise1"

    @patch("backend.repositories.franchise_repo.api_get")
    def test_get_all_franchises_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = get_all_franchises()

        assert result == []

    @patch("backend.repositories.franchise_repo.api_post")
    def test_add_franchise_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = add_franchise(
            "Contact Person",
            "Org",
            "+1234567890",
            "test@example.com",
            "Address",
            "2024-01-01",
            "2025-01-01",
            "active",
            10.5,
            1000.0,
            500.0,
        )

        assert result is True
        mock_post.assert_called_once()

    @patch("backend.repositories.franchise_repo.api_post")
    def test_add_franchise_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = add_franchise(
            "Contact Person",
            "Org",
            "+1234567890",
            "test@example.com",
            "Address",
            "2024-01-01",
            "2025-01-01",
            "active",
            10.5,
            1000.0,
            500.0,
        )

        assert result is False
