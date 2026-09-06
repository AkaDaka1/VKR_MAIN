"""
Тесты для сервисов (backend/services)
Тестирует бизнес-логику сервисов
"""
import pytest
from unittest.mock import patch, MagicMock
from backend.services.employee_service import (
    load_employees,
    remove_employee_by_login,
    update_employee_last_online
)
from backend.services.franchise_service import (
    load_franchises,
    create_new_franchise
)


class TestEmployeeService:
    """Тесты для сервиса сотрудников"""

    @patch('backend.services.employee_service.get_all_employees')
    def test_load_employees(self, mock_get_all):
        mock_get_all.return_value = [
            {"id": 1, "username": "user1", "role": "admin", "last_online": "2024-01-01"},
            {"id": 2, "username": "user2", "role": "user", "last_online": "2024-01-02"}
        ]

        result = load_employees()

        assert len(result) == 2
        assert result[0]["username"] == "user1"
        assert result[0]["role"] == "admin"
        mock_get_all.assert_called_once()

    @patch('backend.services.employee_service.get_all_employees')
    def test_load_employees_empty(self, mock_get_all):
        mock_get_all.return_value = []

        result = load_employees()

        assert result == []

    @patch('backend.services.employee_service.delete_employee_by_login')
    def test_remove_employee_by_login(self, mock_delete):
        mock_delete.return_value = True

        result = remove_employee_by_login("testuser")

        assert result is True
        mock_delete.assert_called_once_with("testuser")

    @patch('backend.services.employee_service.update_last_online')
    def test_update_employee_last_online(self, mock_update):
        mock_update.return_value = True

        result = update_employee_last_online("testuser")

        assert result is True
        mock_update.assert_called_once_with("testuser")


class TestFranchiseService:
    """Тесты для сервиса франшиз"""

    @patch('backend.services.franchise_service.get_all_franchises')
    def test_load_franchises(self, mock_get_all):
        mock_get_all.return_value = [
            {
                "contract_id": 1,
                "contact_person": "Person1",
                "organization": "Org1",
                "phone": "+1234567890",
                "email": "org1@example.com",
                "address": "Address1",
                "start_date": "2024-01-01",
                "end_date": "2025-01-01",
                "status": "active",
                "royalty_percentage": 10.5,
                "initial_fee": 1000.0,
                "monthly_fee": 500.0
            },
            {
                "contract_id": 2,
                "contact_person": "Person2",
                "organization": "Org2",
                "phone": "+9876543210",
                "email": "org2@example.com",
                "address": "Address2",
                "start_date": "2024-02-01",
                "end_date": "2025-02-01",
                "status": "inactive",
                "royalty_percentage": 15.0,
                "initial_fee": 2000.0,
                "monthly_fee": 750.0
            }
        ]

        result = load_franchises()

        assert len(result) == 2
        assert result[0]["organization"] == "Org1"
        assert result[1]["status"] == "inactive"
        mock_get_all.assert_called_once()

    @patch('backend.services.franchise_service.get_all_franchises')
    def test_load_franchises_empty(self, mock_get_all):
        mock_get_all.return_value = []

        result = load_franchises()

        assert result == []

    @patch('backend.services.franchise_service.add_franchise')
    def test_create_new_franchise(self, mock_add):
        mock_add.return_value = True

        result = create_new_franchise(
            "Contact Person", "Org", "+1234567890",
            "test@example.com", "Address", "2024-01-01",
            "2025-01-01", "active", 10.5, 1000.0, 500.0
        )

        assert result is True
        mock_add.assert_called_once_with(
            "Contact Person", "Org", "+1234567890",
            "test@example.com", "Address", "2024-01-01",
            "2025-01-01", "active", 10.5, 1000.0, 500.0
        )

    @patch('backend.services.franchise_service.add_franchise')
    def test_create_new_franchise_failure(self, mock_add):
        mock_add.return_value = False

        result = create_new_franchise(
            "Contact Person", "Org", "+1234567890",
            "test@example.com", "Address", "2024-01-01",
            "2025-01-01", "active", 10.5, 1000.0, 500.0
        )

        assert result is False
