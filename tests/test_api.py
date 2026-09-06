"""
Тесты для API эндпоинтов
Использует TestClient для тестирования без запуска сервера
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from unittest.mock import MagicMock

from api.auth import get_current_user
from api.database import Base, get_db
from api.api import app


async def override_get_current_user_admin():
    u = MagicMock()
    u.role = "admin"
    u.username = "apitest_admin"
    u.id = 1
    u.last_online = None
    return u

# Создаем тестовую базу данных в памяти (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Создаем таблицы в тестовой БД
Base.metadata.create_all(bind=engine)

# Переопределяем зависимость
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user_admin

client = TestClient(app)


class TestEmployeeEndpoints:
    """Тесты для эндпоинтов сотрудников"""

    def test_create_employee(self):
        response = client.post(
            "/employees/",
            json={
                "username": "testuser",
                "password": "testpass123",
                "role": "admin"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "admin"
        assert "id" in data

    def test_get_employees(self):
        response = client.get("/employees/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_employee_by_id(self):
        # Сначала создаем сотрудника
        create_response = client.post(
            "/employees/",
            json={
                "username": "gettestuser",
                "password": "testpass123",
                "role": "user"
            }
        )
        assert create_response.status_code in [200, 201]
        employee_id = create_response.json()["id"]

        # Получаем сотрудника по ID
        response = client.get(f"/employees/{employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "gettestuser"

    def test_delete_employee(self):
        # Создаем сотрудника
        create_response = client.post(
            "/employees/",
            json={
                "username": "deletetestuser",
                "password": "testpass123",
                "role": "user"
            }
        )
        employee_id = create_response.json()["id"]

        # Удаляем
        delete_response = client.delete(f"/employees/{employee_id}")
        assert delete_response.status_code == 200

        # Проверяем, что удален
        get_response = client.get(f"/employees/{employee_id}")
        assert get_response.status_code == 404


class TestFranchiseEndpoints:
    """Тесты для эндпоинтов франшиз"""

    def test_create_franchise(self):
        response = client.post(
            "/franchises/",
            json={
                "contact_person": "Test Contact",
                "organization": "Test Org",
                "phone": "+1234567890",
                "email": "test@example.com",
                "address": "Test Address",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2025-01-01T00:00:00",
                "status": "active",
                "royalty_percentage": 10.5,
                "initial_fee": 1000.0,
                "monthly_fee": 500.0
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["organization"] == "Test Org"
        assert "contract_id" in data

    def test_get_franchises(self):
        response = client.get("/franchises/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_update_franchise(self):
        # Создаем франшизу
        create_response = client.post(
            "/franchises/",
            json={
                "contact_person": "Update Contact",
                "organization": "Update Org",
                "phone": "+1234567890",
                "email": "update@example.com",
                "address": "Update Address",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2025-01-01T00:00:00",
                "status": "active",
                "royalty_percentage": 10.5,
                "initial_fee": 1000.0,
                "monthly_fee": 500.0
            }
        )
        franchise_id = create_response.json()["contract_id"]

        # Обновляем
        update_response = client.put(
            f"/franchises/{franchise_id}",
            json={
                "contact_person": "Updated Contact",
                "organization": "Updated Org",
                "phone": "+9876543210",
                "email": "updated@example.com",
                "address": "Updated Address",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2025-01-01T00:00:00",
                "status": "inactive",
                "royalty_percentage": 15.0,
                "initial_fee": 2000.0,
                "monthly_fee": 750.0
            }
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["organization"] == "Updated Org"

    def test_delete_franchise(self):
        # Создаем франшизу
        create_response = client.post(
            "/franchises/",
            json={
                "contact_person": "Delete Contact",
                "organization": "Delete Org",
                "phone": "+1234567890",
                "email": "delete@example.com",
                "address": "Delete Address",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2025-01-01T00:00:00",
                "status": "active",
                "royalty_percentage": 10.5,
                "initial_fee": 1000.0,
                "monthly_fee": 500.0
            }
        )
        franchise_id = create_response.json()["contract_id"]

        # Удаляем
        delete_response = client.delete(f"/franchises/{franchise_id}")
        assert delete_response.status_code == 200


class TestTheaterEndpoints:
    """Тесты для эндпоинтов театров"""

    def test_create_theater(self):
        response = client.post(
            "/theaters/",
            json={
                "contract_id": 1,
                "name": "Test Theater",
                "location": "Test Location"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Test Theater"

    def test_get_theaters(self):
        response = client.get("/theaters/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestHallEndpoints:
    """Тесты для эндпоинтов залов"""

    def test_create_hall(self):
        # Сначала создаем театр
        client.post(
            "/theaters/",
            json={
                "contract_id": 2,
                "name": "Hall Theater",
                "location": "Hall Location"
            }
        )
        
        response = client.post(
            "/halls/",
            json={
                "theater_id": 1,
                "capacity": 100
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["capacity"] == 100

    def test_get_halls(self):
        response = client.get("/halls/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestScenarioEndpoints:
    """Тесты для эндпоинтов сценариев"""

    def test_create_scenario(self):
        response = client.post(
            "/scenarios/",
            json={
                "title": "Test Scenario",
                "status": "active",
                "description": "Test Description"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "Test Scenario"

    def test_get_scenarios(self):
        response = client.get("/scenarios/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestShowEndpoints:
    """Тесты для эндпоинтов шоу"""

    @pytest.mark.skip(reason="SQLite не поддерживает тип INTERVAL — тест работает только с PostgreSQL")
    def test_create_show(self):
        response = client.post(
            "/shows/",
            json={
                "hall_id": 1,
                "scenario_id": 1,
                "title": "Test Show",
                "vote_type": "common",
                "duration": "02:00:00",
                "show_date": "2024-12-01T19:00:00"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["title"] == "Test Show"

    def test_get_shows(self):
        response = client.get("/shows/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestCustomerEndpoints:
    """Тесты для эндпоинтов клиентов"""

    def test_create_customer(self):
        response = client.post(
            "/customers/",
            json={
                "email": "test@example.com",
                "phone": "+1234567890"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_customers(self):
        response = client.get("/customers/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTicketEndpoints:
    """Тесты для эндпоинтов билетов"""

    def test_create_ticket(self):
        response = client.post(
            "/tickets/",
            json={
                "owner_id": 1,
                "show_id": 1,
                "seat_number": "A1",
                "price": 1000.0,
                "status": "available",
                "vip_status": False,
                "email": "test@example.com"
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["seat_number"] == "A1"

    def test_get_tickets(self):
        response = client.get("/tickets/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestEquipmentEndpoints:
    """Тесты для эндпоинтов оборудования"""

    def test_create_equipment(self):
        response = client.post(
            "/equipments/",
            json={
                "name": "Test Equipment",
                "price": 5000.0,
                "amount": 10
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Test Equipment"

    def test_get_equipments(self):
        response = client.get("/equipments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestServiceEndpoints:
    """Тесты для эндпоинтов сервисов"""

    def test_create_service(self):
        response = client.post(
            "/services/",
            json={
                "name": "Test Service",
                "price": 1000.0,
                "amount": 5
            }
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["name"] == "Test Service"

    def test_get_services(self):
        response = client.get("/services/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAuthentication:
    """Тесты для аутентификации"""

    def test_login_success(self):
        # Сначала создаем пользователя
        client.post(
            "/employees/",
            json={
                "username": "logintestuser",
                "password": "securepass123",
                "role": "admin"
            }
        )

        # Пробуем залогиниться
        response = client.post(
            "/token",
            data={
                "username": "logintestuser",
                "password": "securepass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        response = client.post(
            "/token",
            data={
                "username": "wronguser",
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401


class TestRolePermissions:
    def test_get_role_permissions(self):
        response = client.get("/role-permissions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "admin" in data
        assert "manager" in data
        assert data["admin"].get("employee_read") is True

    def test_put_role_permissions(self):
        from app.roles import PERMISSION_EMPLOYEE_READ, PERMISSION_KEYS

        body = {
            "manager": {k: False for k in PERMISSION_KEYS},
        }
        body["manager"][PERMISSION_EMPLOYEE_READ] = True
        response = client.put("/role-permissions", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["manager"][PERMISSION_EMPLOYEE_READ] is True


class TestPublicClientEndpoints:
    def _register_and_login(self, email: str = "mobile@example.com", password: str = "pass12345") -> str:
        reg = client.post(
            "/public/v1/auth/register",
            json={"email": email, "phone": "+79990001122", "password": password},
        )
        assert reg.status_code in [200, 201]
        login = client.post("/public/v1/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json().get("access_token")
        assert token
        return token

    def test_public_theaters_and_shows(self):
        theater = client.post("/theaters/", json={"contract_id": 777, "name": "Public Theater", "location": "Center"})
        assert theater.status_code in [200, 201]
        theater_id = theater.json()["theater_id"]
        halls = client.post("/halls/", json={"theater_id": theater_id, "capacity": 100})
        assert halls.status_code in [200, 201]
        hall_id = halls.json()["hall_id"]
        show = client.post(
            "/shows/",
            json={"hall_id": hall_id, "title": "Public Show", "show_date": "2026-05-01T19:00:00"},
        )
        assert show.status_code in [200, 201]

        theaters = client.get("/public/v1/theaters")
        assert theaters.status_code == 200
        assert isinstance(theaters.json(), list)

        shows = client.get(f"/public/v1/theaters/{theater_id}/shows")
        assert shows.status_code == 200
        assert isinstance(shows.json(), list)

    def test_public_reservation_flow(self):
        token = self._register_and_login()
        headers = {"Authorization": f"Bearer {token}"}
        theater = client.post("/theaters/", json={
            "contract_id": 888,"name": "Reserve Theater", "location": "North"})
        assert theater.status_code in [200, 201]
        theater_id = theater.json()["theater_id"]
        hall = client.post("/halls/", json={"theater_id": theater_id, "capacity": 120})
        assert hall.status_code in [200, 201]
        hall_id = hall.json()["hall_id"]
        show_resp = client.post("/shows/",
            json={"hall_id": hall_id, "title": "Reserve Show", "show_date": "2026-06-01T19:00:00"},
        )
        assert show_resp.status_code in [200, 201]
        show_id = show_resp.json()["show_id"]
        customer_resp = client.post("/customers/",json={"email": "mobile@example.com", "phone": "+79990001122"})
        assert customer_resp.status_code in [200, 201, 400]
        ticket_resp = client.post(
            "/tickets/",
            json={
                "show_id": show_id,
                "seat_number": "A1",
                "price": 1000.0,
                "status": "available",
                "vip_status": False,
                "email": "mobile@example.com",
            },
        )
        assert ticket_resp.status_code in [200, 201]

        seats_resp = client.get(f"/public/v1/shows/{show_id}/seats")
        assert seats_resp.status_code == 200
        assert any(seat["seat_number"] == "A1" for seat in seats_resp.json())

        reserve = client.post(
            "/public/v1/reservations",
            json={"show_id": show_id, "seat_number": "A1"},
            headers=headers,
        )
        assert reserve.status_code == 200
        assert reserve.json()["status"] == "booked"

        reserve_again = client.post(
            "/public/v1/reservations",
            json={"show_id": show_id, "seat_number": "A1"},
            headers=headers,
        )
        assert reserve_again.status_code == 409

        my_reservations = client.get("/public/v1/reservations/my", headers=headers)
        assert my_reservations.status_code == 200
        assert len(my_reservations.json()) >= 1











