from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import bcrypt
from datetime import datetime
from typing import List, Optional

from app.roles import ALL_ROLES, PERMISSION_KEYS, ROLE_ADMIN, normalize_role, static_permission_row

from . import models, schemas


# Операции для Employee
def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()


def get_employee_by_username(db: Session, username: str):
    return db.query(models.Employee).filter(models.Employee.username == username).first()


def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Employee).offset(skip).limit(limit).all()


def create_employee(db: Session, employee: schemas.EmployeeCreate):
    # Хешируем пароль
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(employee.password.encode(), salt)
    
    db_employee = models.Employee(
        username=employee.username,
        password=hashed_password.decode('utf-8'),
        role=employee.role
    )
    db.add(db_employee)
    try:
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )


def update_employee_last_online(db: Session, username: str):
    employee = get_employee_by_username(db, username)
    if employee:
        employee.last_online = datetime.now()
        db.commit()
        db.refresh(employee)
        return employee
    return None


def delete_employee(db: Session, employee_id: int):
    db_employee = get_employee(db, employee_id)
    if db_employee:
        db.delete(db_employee)
        db.commit()
        return True
    return False


def update_employee(db: Session, employee_id: int, employee: schemas.EmployeeUpdate):
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None

    payload = employee.model_dump(exclude_unset=True)
    if "password" in payload and payload["password"]:
        salt = bcrypt.gensalt()
        payload["password"] = bcrypt.hashpw(payload["password"].encode(), salt).decode("utf-8")
    elif "password" in payload:
        payload.pop("password")

    for key, value in payload.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)
    return db_employee


def authenticate_employee(db: Session, username: str, password: str):
    employee = get_employee_by_username(db, username)
    if not employee:
        return None
    
    # Проверяем пароль
    if isinstance(employee.password, str):
        if employee.password.startswith('\\x'):
            # Убираем префикс \x и декодируем шестнадцатеричную строку в байты
            hex_part = employee.password[2:]
            hashed = bytes.fromhex(hex_part)
        else:
            # Просто строка, преобразуем в байты
            hashed = employee.password.encode('utf-8')
    elif isinstance(employee.password, bytes):
        hashed = employee.password
    else:
        return None

    if bcrypt.checkpw(password.encode(), hashed):
        # Обновляем время последнего онлайн
        update_employee_last_online(db, username)
        return employee
    
    return None


# Операции для Franchise
def get_franchise(db: Session, franchise_id: int):
    return db.query(models.Franchise).filter(models.Franchise.contract_id == franchise_id).first()


def get_franchises(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Franchise).offset(skip).limit(limit).all()


def create_franchise(db: Session, franchise: schemas.FranchiseCreate):
    db_franchise = models.Franchise(**franchise.model_dump())
    db.add(db_franchise)
    db.commit()
    db.refresh(db_franchise)
    return db_franchise


def update_franchise(db: Session, franchise_id: int, franchise: schemas.FranchiseCreate):
    db_franchise = get_franchise(db, franchise_id)
    if db_franchise:
        for key, value in franchise.model_dump().items():
            setattr(db_franchise, key, value)
        db.commit()
        db.refresh(db_franchise)
        return db_franchise
    return None


def delete_franchise(db: Session, franchise_id: int):
    db_franchise = get_franchise(db, franchise_id)
    if db_franchise:
        db.delete(db_franchise)
        db.commit()
        return True
    return False


# Операции для Theater
def get_theater(db: Session, theater_id: int):
    return db.query(models.Theater).filter(models.Theater.theater_id == theater_id).first()


def get_theaters(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Theater).offset(skip).limit(limit).all()


def create_theater(db: Session, theater: schemas.TheaterCreate):
    db_theater = models.Theater(**theater.model_dump())
    db.add(db_theater)
    db.commit()
    db.refresh(db_theater)
    return db_theater


def delete_theater(db: Session, theater_id: int):
    db_theater = get_theater(db, theater_id)
    if db_theater:
        db.delete(db_theater)
        db.commit()
        return True
    return False


def update_theater(db: Session, theater_id: int, theater: schemas.TheaterCreate):
    db_theater = get_theater(db, theater_id)
    if not db_theater:
        return None
    for key, value in theater.model_dump().items():
        setattr(db_theater, key, value)
    db.commit()
    db.refresh(db_theater)
    return db_theater


# Операции для Hall
def get_hall(db: Session, hall_id: int):
    return db.query(models.Hall).filter(models.Hall.hall_id == hall_id).first()


def get_halls(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Hall).offset(skip).limit(limit).all()


def create_hall(db: Session, hall: schemas.HallCreate):
    db_hall = models.Hall(**hall.model_dump())
    db.add(db_hall)
    db.commit()
    db.refresh(db_hall)
    return db_hall


def delete_hall(db: Session, hall_id: int):
    db_hall = get_hall(db, hall_id)
    if db_hall:
        db.delete(db_hall)
        db.commit()
        return True
    return False


def update_hall(db: Session, hall_id: int, hall: schemas.HallCreate):
    db_hall = get_hall(db, hall_id)
    if not db_hall:
        return None
    for key, value in hall.model_dump().items():
        setattr(db_hall, key, value)
    db.commit()
    db.refresh(db_hall)
    return db_hall


# Операции для Scenario
def get_scenario(db: Session, scenario_id: int):
    return db.query(models.Scenario).filter(models.Scenario.scenario_id == scenario_id).first()


def get_scenarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Scenario).offset(skip).limit(limit).all()


def create_scenario(db: Session, scenario: schemas.ScenarioCreate):
    db_scenario = models.Scenario(**scenario.model_dump())
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


def attach_scenario_tz_source(db: Session, scenario_id: int, orig_name: str, relpath: str):
    from . import scenario_files

    s = get_scenario(db, scenario_id)
    if not s:
        return None
    scenario_files.delete_stored_files(s.tz_source_relpath, s.tz_result_relpath)
    s.tz_source_filename = orig_name
    s.tz_source_relpath = relpath
    s.tz_result_filename = None
    s.tz_result_relpath = None
    s.tz_pipeline_status = "uploaded"
    db.commit()
    db.refresh(s)
    return s


def attach_scenario_tz_result(db: Session, scenario_id: int, orig_name: str, relpath: str, status: str = "ready"):
    from . import scenario_files

    s = get_scenario(db, scenario_id)
    if not s:
        return None
    scenario_files.delete_stored_files(None, s.tz_result_relpath)
    s.tz_result_filename = orig_name
    s.tz_result_relpath = relpath
    s.tz_pipeline_status = status
    db.commit()
    db.refresh(s)
    return s


def set_scenario_tz_pipeline_status(db: Session, scenario_id: int, status: str):
    s = get_scenario(db, scenario_id)
    if not s:
        return None
    s.tz_pipeline_status = status
    db.commit()
    db.refresh(s)
    return s


def delete_scenario(db: Session, scenario_id: int):
    from . import scenario_files

    db_scenario = get_scenario(db, scenario_id)
    if db_scenario:
        scenario_files.delete_stored_files(db_scenario.tz_source_relpath, db_scenario.tz_result_relpath)
        db.delete(db_scenario)
        db.commit()
        return True
    return False


# Операции для Act
def get_act(db: Session, act_id: int):
    return db.query(models.Act).filter(models.Act.id == act_id).first()


def get_acts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Act).offset(skip).limit(limit).all()


def create_act(db: Session, act: schemas.ActCreate):
    db_act = models.Act(**act.model_dump())
    db.add(db_act)
    db.commit()
    db.refresh(db_act)
    return db_act


def delete_act(db: Session, act_id: int):
    db_act = get_act(db, act_id)
    if db_act:
        db.delete(db_act)
        db.commit()
        return True
    return False


# Операции для Part
def get_part(db: Session, part_id: int):
    return db.query(models.Part).filter(models.Part.id == part_id).first()


def get_parts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Part).offset(skip).limit(limit).all()


def create_part(db: Session, part: schemas.PartCreate):
    db_part = models.Part(**part.model_dump())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part


def delete_part(db: Session, part_id: int):
    db_part = get_part(db, part_id)
    if db_part:
        db.delete(db_part)
        db.commit()
        return True
    return False


# Операции для Show
def get_show(db: Session, show_id: int):
    return db.query(models.Show).filter(models.Show.show_id == show_id).first()


def get_shows(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Show).offset(skip).limit(limit).all()


def create_show(db: Session, show: schemas.ShowCreate):
    db_show = models.Show(**show.model_dump())
    db.add(db_show)
    db.commit()
    db.refresh(db_show)
    return db_show


def delete_show(db: Session, show_id: int):
    db_show = get_show(db, show_id)
    if db_show:
        db.delete(db_show)
        db.commit()
        return True
    return False


def update_show(db: Session, show_id: int, show: schemas.ShowCreate):
    db_show = get_show(db, show_id)
    if not db_show:
        return None
    for key, value in show.model_dump().items():
        setattr(db_show, key, value)
    db.commit()
    db.refresh(db_show)
    return db_show


# Операции для Customer
def get_customer(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()


def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()


def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    try:
        db.commit()
        db.refresh(db_customer)
        return db_customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )


def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()


def create_customer_account(db: Session, customer: schemas.PublicCustomerRegister):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(customer.password.encode(), salt).decode("utf-8")
    db_customer = models.Customer(
        email=customer.email,
        phone=customer.phone,
        password=hashed_password,
        is_active=True,
    )
    db.add(db_customer)
    try:
        db.commit()
        db.refresh(db_customer)
        return db_customer
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )


def authenticate_customer(db: Session, email: str, password: str):
    customer = get_customer_by_email(db, email)
    if not customer or not customer.password or not customer.is_active:
        return None
    hashed = customer.password.encode("utf-8")
    if bcrypt.checkpw(password.encode(), hashed):
        return customer
    return None


def reserve_ticket_for_customer(db: Session, show_id: int, seat_number: str, customer_email: str):
    ticket = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.show_id == show_id,
            models.Ticket.seat_number == seat_number,
            models.Ticket.status == "available",
        )
        .with_for_update()
        .first()
    )
    if not ticket:
        return None
    ticket.status = "booked"
    ticket.email = customer_email
    db.commit()
    db.refresh(ticket)
    return ticket


def get_customer_reservations(db: Session, customer_email: str):
    return (
        db.query(models.Ticket)
        .filter(models.Ticket.email == customer_email, models.Ticket.status == "booked")
        .all()
    )


def delete_customer(db: Session, email: str):
    db_customer = get_customer(db, email)
    if db_customer:
        db.delete(db_customer)
        db.commit()
        return True
    return False


# Операции для Ticket
def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()


def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ticket).offset(skip).limit(limit).all()


def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int):
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket:
        db.delete(db_ticket)
        db.commit()
        return True
    return False


def update_ticket(db: Session, ticket_id: int, ticket: schemas.TicketCreate):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    for key, value in ticket.model_dump().items():
        setattr(db_ticket, key, value)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


# Операции для Vote_Common
def get_vote_common(db: Session, ticket_id: int, vote_id: int):
    return db.query(models.Vote_Common).filter(
        models.Vote_Common.ticket_id == ticket_id,
        models.Vote_Common.vote_id == vote_id
    ).first()


def get_votes_common(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Vote_Common).offset(skip).limit(limit).all()


def create_vote_common(db: Session, vote_common: schemas.VoteCommonCreate):
    db_vote_common = models.Vote_Common(**vote_common.model_dump())
    db.add(db_vote_common)
    db.commit()
    db.refresh(db_vote_common)
    return db_vote_common


def delete_vote_common(db: Session, ticket_id: int, vote_id: int):
    db_vote_common = get_vote_common(db, ticket_id, vote_id)
    if db_vote_common:
        db.delete(db_vote_common)
        db.commit()
        return True
    return False


# Операции для Vote_VIP
def get_vote_vip(db: Session, vote_id: int):
    return db.query(models.Vote_VIP).filter(models.Vote_VIP.vote_id == vote_id).first()


def get_votes_vip(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Vote_VIP).offset(skip).limit(limit).all()


def create_vote_vip(db: Session, vote_vip: schemas.VoteVIPCreate):
    db_vote_vip = models.Vote_VIP(**vote_vip.model_dump())
    db.add(db_vote_vip)
    db.commit()
    db.refresh(db_vote_vip)
    return db_vote_vip


def delete_vote_vip(db: Session, vote_id: int):
    db_vote_vip = get_vote_vip(db, vote_id)
    if db_vote_vip:
        db.delete(db_vote_vip)
        db.commit()
        return True
    return False


# Операции для Equipment
def get_equipment(db: Session, equipment_id: int):
    return db.query(models.Equipment).filter(models.Equipment.equipment_id == equipment_id).first()


def get_equipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Equipment).offset(skip).limit(limit).all()


def create_equipment(db: Session, equipment: schemas.EquipmentCreate):
    db_equipment = models.Equipment(**equipment.model_dump())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment


def delete_equipment(db: Session, equipment_id: int):
    db_equipment = get_equipment(db, equipment_id)
    if db_equipment:
        db.delete(db_equipment)
        db.commit()
        return True
    return False


# Операции для Rent_Equipment
def get_rent_equipment(db: Session, equipment_id: int, show_id: int):
    return db.query(models.Rent_Equipment).filter(
        models.Rent_Equipment.equipment_id == equipment_id,
        models.Rent_Equipment.show_id == show_id
    ).first()


def get_rents_equipment(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rent_Equipment).offset(skip).limit(limit).all()


def create_rent_equipment(db: Session, rent_equipment: schemas.RentEquipmentCreate):
    db_rent_equipment = models.Rent_Equipment(**rent_equipment.model_dump())
    db.add(db_rent_equipment)
    db.commit()
    db.refresh(db_rent_equipment)
    return db_rent_equipment


def delete_rent_equipment(db: Session, equipment_id: int, show_id: int):
    db_rent_equipment = get_rent_equipment(db, equipment_id, show_id)
    if db_rent_equipment:
        db.delete(db_rent_equipment)
        db.commit()
        return True
    return False


# Операции для Service
def get_service(db: Session, service_id: int):
    return db.query(models.Service).filter(models.Service.service_id == service_id).first()


def get_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Service).offset(skip).limit(limit).all()


def create_service(db: Session, service: schemas.ServiceCreate):
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


def delete_service(db: Session, service_id: int):
    db_service = get_service(db, service_id)
    if db_service:
        db.delete(db_service)
        db.commit()
        return True
    return False


# Операции для Rent_Service
def get_rent_service(db: Session, service_id: int, show_id: int):
    return db.query(models.Rent_Service).filter(
        models.Rent_Service.service_id == service_id,
        models.Rent_Service.show_id == show_id
    ).first()


def get_rents_service(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Rent_Service).offset(skip).limit(limit).all()


def create_rent_service(db: Session, rent_service: schemas.RentServiceCreate):
    db_rent_service = models.Rent_Service(**rent_service.model_dump())
    db.add(db_rent_service)
    db.commit()
    db.refresh(db_rent_service)
    return db_rent_service


def delete_rent_service(db: Session, service_id: int, show_id: int):
    db_rent_service = get_rent_service(db, service_id, show_id)
    if db_rent_service:
        db.delete(db_rent_service)
        db.commit()
        return True
    return False


# --- Права ролей (RolePermission) ---


def get_merged_permissions_for_role(db: Session, role: str) -> dict[str, bool]:
    r = normalize_role(role)
    merged = dict(static_permission_row(r))
    if r == ROLE_ADMIN:
        return merged
    rows = db.query(models.RolePermission).filter(models.RolePermission.role_slug == r).all()
    for row in rows:
        if row.permission_key in PERMISSION_KEYS:
            merged[row.permission_key] = bool(row.allowed)
    return merged


def user_has_permission(db: Session, role: str, permission_key: str) -> bool:
    merged = get_merged_permissions_for_role(db, role)
    return bool(merged.get(permission_key, False))


def get_full_role_permissions_matrix(db: Session) -> dict[str, dict[str, bool]]:
    return {role: get_merged_permissions_for_role(db, role) for role in sorted(ALL_ROLES)}


def replace_role_permissions_matrix(db: Session, body: dict[str, dict[str, bool]]) -> None:
    db.query(models.RolePermission).delete()
    for role_slug, row in body.items():
        r = normalize_role(role_slug)
        if r == ROLE_ADMIN or r not in ALL_ROLES:
            continue
        defaults = static_permission_row(r)
        for key in PERMISSION_KEYS:
            val = bool(row[key]) if key in row else defaults[key]
            db.add(models.RolePermission(role_slug=r, permission_key=key, allowed=val))
    db.commit()