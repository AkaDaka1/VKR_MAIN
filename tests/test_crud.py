"""
Тесты для CRUD операций (api/crud.py)
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.database import Base
from api import crud, models, schemas


# Создаем тестовую базу данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Фикстура для создания сессии базы данных"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestEmployeeCrud:
    """Тесты для CRUD операций с сотрудниками"""

    def test_create_employee(self, db_session):
        employee = schemas.EmployeeCreate(
            username="testuser",
            password="testpass123",
            role="admin"
        )

        result = crud.create_employee(db_session, employee)

        assert result.username == "testuser"
        assert result.role == "admin"
        assert result.id is not None
        # Проверяем, что пароль захеширован
        assert result.password != "testpass123"
        assert len(result.password) > 50  # bcrypt хеши длинные

    def test_get_employee_by_username(self, db_session):
        # Создаем сотрудника
        employee = schemas.EmployeeCreate(
            username="getuser",
            password="testpass123",
            role="user"
        )
        crud.create_employee(db_session, employee)

        # Получаем по имени
        result = crud.get_employee_by_username(db_session, "getuser")

        assert result is not None
        assert result.username == "getuser"

    def test_get_employee_by_id(self, db_session):
        employee = schemas.EmployeeCreate(
            username="getiduser",
            password="testpass123",
            role="user"
        )
        created = crud.create_employee(db_session, employee)

        result = crud.get_employee(db_session, created.id)

        assert result is not None
        assert result.id == created.id

    def test_get_employees(self, db_session):
        # Создаем нескольких сотрудников
        for i in range(3):
            employee = schemas.EmployeeCreate(
                username=f"user{i}",
                password="testpass123",
                role="user"
            )
            crud.create_employee(db_session, employee)

        result = crud.get_employees(db_session)

        assert len(result) == 3

    def test_delete_employee(self, db_session):
        employee = schemas.EmployeeCreate(
            username="deleteuser",
            password="testpass123",
            role="user"
        )
        created = crud.create_employee(db_session, employee)

        result = crud.delete_employee(db_session, created.id)

        assert result is True
        # Проверяем, что сотрудник удален
        assert crud.get_employee(db_session, created.id) is None

    def test_delete_nonexistent_employee(self, db_session):
        result = crud.delete_employee(db_session, 9999)
        assert result is False

    def test_create_duplicate_employee(self, db_session):
        employee = schemas.EmployeeCreate(
            username="duplicateuser",
            password="testpass123",
            role="user"
        )
        crud.create_employee(db_session, employee)

        # Пытаемся создать еще одного с тем же именем
        with pytest.raises(Exception):
            crud.create_employee(db_session, employee)


class TestFranchiseCrud:
    """Тесты для CRUD операций с франшизами"""

    def test_create_franchise(self, db_session):
        franchise = schemas.FranchiseCreate(
            contact_person="Test Contact",
            organization="Test Org",
            phone="+1234567890",
            email="test@example.com",
            address="Test Address",
            start_date="2024-01-01T00:00:00",
            end_date="2025-01-01T00:00:00",
            status="active",
            royalty_percentage=10.5,
            initial_fee=1000.0,
            monthly_fee=500.0
        )

        result = crud.create_franchise(db_session, franchise)

        assert result.organization == "Test Org"
        assert result.contact_person == "Test Contact"
        assert result.contract_id is not None

    def test_get_franchise(self, db_session):
        franchise = schemas.FranchiseCreate(
            contact_person="Get Contact",
            organization="Get Org",
            phone="+1234567890",
            email="get@example.com",
            address="Get Address",
            start_date="2024-01-01T00:00:00",
            end_date="2025-01-01T00:00:00",
            status="active",
            royalty_percentage=10.5,
            initial_fee=1000.0,
            monthly_fee=500.0
        )
        created = crud.create_franchise(db_session, franchise)

        result = crud.get_franchise(db_session, created.contract_id)

        assert result is not None
        assert result.organization == "Get Org"

    def test_get_franchises(self, db_session):
        for i in range(3):
            franchise = schemas.FranchiseCreate(
                contact_person=f"Contact {i}",
                organization=f"Org {i}",
                phone="+1234567890",
                email=f"org{i}@example.com",
                address=f"Address {i}",
                start_date="2024-01-01T00:00:00",
                end_date="2025-01-01T00:00:00",
                status="active",
                royalty_percentage=10.5,
                initial_fee=1000.0,
                monthly_fee=500.0
            )
            crud.create_franchise(db_session, franchise)

        result = crud.get_franchises(db_session)

        assert len(result) == 3

    def test_update_franchise(self, db_session):
        franchise = schemas.FranchiseCreate(
            contact_person="Update Contact",
            organization="Update Org",
            phone="+1234567890",
            email="update@example.com",
            address="Update Address",
            start_date="2024-01-01T00:00:00",
            end_date="2025-01-01T00:00:00",
            status="active",
            royalty_percentage=10.5,
            initial_fee=1000.0,
            monthly_fee=500.0
        )
        created = crud.create_franchise(db_session, franchise)

        # Обновляем
        updated_franchise = schemas.FranchiseCreate(
            contact_person="Updated Contact",
            organization="Updated Org",
            phone="+9876543210",
            email="updated@example.com",
            address="Updated Address",
            start_date="2024-01-01T00:00:00",
            end_date="2025-01-01T00:00:00",
            status="inactive",
            royalty_percentage=15.0,
            initial_fee=2000.0,
            monthly_fee=750.0
        )

        result = crud.update_franchise(db_session, created.contract_id, updated_franchise)

        assert result is not None
        assert result.organization == "Updated Org"
        assert result.status == "inactive"

    def test_delete_franchise(self, db_session):
        franchise = schemas.FranchiseCreate(
            contact_person="Delete Contact",
            organization="Delete Org",
            phone="+1234567890",
            email="delete@example.com",
            address="Delete Address",
            start_date="2024-01-01T00:00:00",
            end_date="2025-01-01T00:00:00",
            status="active",
            royalty_percentage=10.5,
            initial_fee=1000.0,
            monthly_fee=500.0
        )
        created = crud.create_franchise(db_session, franchise)

        result = crud.delete_franchise(db_session, created.contract_id)

        assert result is True
        assert crud.get_franchise(db_session, created.contract_id) is None


class TestTheaterCrud:
    """Тесты для CRUD операций с театрами"""

    def test_create_theater(self, db_session):
        theater = schemas.TheaterCreate(
            contract_id=1,
            name="Test Theater",
            location="Test Location"
        )

        result = crud.create_theater(db_session, theater)

        assert result.name == "Test Theater"
        assert result.theater_id is not None

    def test_get_theaters(self, db_session):
        for i in range(3):
            theater = schemas.TheaterCreate(
                contract_id=i+10,
                name=f"Theater {i}",
                location=f"Location {i}"
            )
            crud.create_theater(db_session, theater)

        result = crud.get_theaters(db_session)

        assert len(result) == 3


class TestHallCrud:
    """Тесты для CRUD операций с залами"""

    def test_create_hall(self, db_session):
        hall = schemas.HallCreate(
            theater_id=1,
            capacity=100
        )

        result = crud.create_hall(db_session, hall)

        assert result.capacity == 100
        assert result.hall_id is not None

    def test_get_halls(self, db_session):
        for i in range(3):
            hall = schemas.HallCreate(
                theater_id=i+1,
                capacity=100 + i*50
            )
            crud.create_hall(db_session, hall)

        result = crud.get_halls(db_session)

        assert len(result) == 3


class TestScenarioCrud:
    """Тесты для CRUD операций со сценариями"""

    def test_create_scenario(self, db_session):
        scenario = schemas.ScenarioCreate(
            title="Test Scenario",
            status="active",
            description="Test Description"
        )

        result = crud.create_scenario(db_session, scenario)

        assert result.title == "Test Scenario"
        assert result.scenario_id is not None

    def test_get_scenarios(self, db_session):
        for i in range(3):
            scenario = schemas.ScenarioCreate(
                title=f"Scenario {i}",
                status="active",
                description=f"Description {i}"
            )
            crud.create_scenario(db_session, scenario)

        result = crud.get_scenarios(db_session)

        assert len(result) == 3


class TestCustomerCrud:
    """Тесты для CRUD операций с клиентами"""

    def test_create_customer(self, db_session):
        customer = schemas.CustomerCreate(
            email="test@example.com",
            phone="+1234567890"
        )

        result = crud.create_customer(db_session, customer)

        assert result.email == "test@example.com"

    def test_get_customer_by_email(self, db_session):
        customer = schemas.CustomerCreate(
            email="get@example.com",
            phone="+1234567890"
        )
        crud.create_customer(db_session, customer)

        result = crud.get_customer(db_session, "get@example.com")

        assert result is not None
        assert result.email == "get@example.com"

    def test_get_customers(self, db_session):
        for i in range(3):
            customer = schemas.CustomerCreate(
                email=f"customer{i}@example.com",
                phone=f"+123456789{i}"
            )
            crud.create_customer(db_session, customer)

        result = crud.get_customers(db_session)

        assert len(result) == 3


class TestEquipmentCrud:
    """Тесты для CRUD операций с оборудованием"""

    def test_create_equipment(self, db_session):
        equipment = schemas.EquipmentCreate(
            name="Test Equipment",
            price=5000.0,
            amount=10
        )

        result = crud.create_equipment(db_session, equipment)

        assert result.name == "Test Equipment"
        assert result.equipment_id is not None

    def test_get_equipments(self, db_session):
        for i in range(3):
            equipment = schemas.EquipmentCreate(
                name=f"Equipment {i}",
                price=1000.0 * (i+1),
                amount=10 + i
            )
            crud.create_equipment(db_session, equipment)

        result = crud.get_equipments(db_session)

        assert len(result) == 3


class TestServiceCrud:
    """Тесты для CRUD операций с сервисами"""

    def test_create_service(self, db_session):
        service = schemas.ServiceCreate(
            name="Test Service",
            price=1000.0,
            amount=5
        )

        result = crud.create_service(db_session, service)

        assert result.name == "Test Service"
        assert result.service_id is not None

    def test_get_services(self, db_session):
        for i in range(3):
            service = schemas.ServiceCreate(
                name=f"Service {i}",
                price=500.0 * (i+1),
                amount=5 + i
            )
            crud.create_service(db_session, service)

        result = crud.get_services(db_session)

        assert len(result) == 3
