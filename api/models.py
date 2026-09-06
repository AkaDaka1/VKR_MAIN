from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Numeric,
    Boolean,
    ForeignKey,
    Interval,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base


class Employee(Base):
    __tablename__ = "Employee"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    last_online = Column(DateTime, default=datetime.now)
    role = Column(String(64))


class RolePermission(Base):
    """Переопределение прав по ролям (полная строка на пару role+key при сохранении из админки)."""

    __tablename__ = "RolePermission"
    __table_args__ = (UniqueConstraint("role_slug", "permission_key", name="uq_role_permission_key"),)

    id = Column(Integer, primary_key=True, index=True)
    role_slug = Column(String(64), nullable=False, index=True)
    permission_key = Column(String(64), nullable=False)
    allowed = Column(Boolean, nullable=False, default=False)


class Franchise(Base):
    __tablename__ = "Franchise"

    contract_id = Column(Integer, primary_key=True, index=True)
    contact_person = Column(String(100))
    organization = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String)  # TEXT
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50))
    royalty_percentage = Column(Numeric(5, 2))  # NUMERIC(5, 2)
    initial_fee = Column(Numeric(10, 2))  # NUMERIC(10, 2)
    monthly_fee = Column(Numeric(10, 2))  # NUMERIC(10, 2)

    # Связи
    theaters = relationship("Theater", back_populates="franchise")


class Theater(Base):
    __tablename__ = "Theater"

    theater_id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("Franchise.contract_id"))
    name = Column(String(100))
    location = Column(String)  # TEXT

    # Связи
    franchise = relationship("Franchise", back_populates="theaters")
    halls = relationship("Hall", back_populates="theater")


class Hall(Base):
    __tablename__ = "Hall"

    hall_id = Column(Integer, primary_key=True, index=True)
    theater_id = Column(Integer, ForeignKey("Theater.theater_id"))
    capacity = Column(Integer)

    # Связи
    theater = relationship("Theater", back_populates="halls")
    shows = relationship("Show", back_populates="hall")


class Scenario(Base):
    __tablename__ = "Scenario"

    scenario_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50))
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    tz_source_filename = Column(String(500))
    tz_source_relpath = Column(String)  # путь относительно SCENARIO_TZ_UPLOAD_ROOT
    tz_result_filename = Column(String(500))
    tz_result_relpath = Column(String)
    tz_pipeline_status = Column(String(50))  # none | uploaded | pending | ready | error

    # Связи
    acts = relationship("Act", back_populates="scenario")
    shows = relationship("Show", back_populates="scenario")


class Act(Base):
    __tablename__ = "Act"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("Scenario.scenario_id"))
    title = Column(String(255), nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Связи
    scenario = relationship("Scenario", back_populates="acts")
    parts = relationship("Part", back_populates="act")
    votes_vip = relationship("Vote_VIP", back_populates="act")


class Part(Base):
    __tablename__ = "Part"

    id = Column(Integer, primary_key=True, index=True)
    act_id = Column(Integer, ForeignKey("Act.id"))
    title = Column(String(255), nullable=False)
    file_path = Column(String, nullable=False)  # TEXT
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Связи
    act = relationship("Act", back_populates="parts")


class Show(Base):
    __tablename__ = "Show"

    show_id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("Hall.hall_id"))
    scenario_id = Column(Integer, ForeignKey("Scenario.scenario_id"))
    title = Column(String(100))
    vote_type = Column(String(100))  # CHECK (vote_type IN ('common', 'vip', 'both'))
    duration = Column(Interval)  # INTERVAL
    show_date = Column(DateTime)

    # Связи
    hall = relationship("Hall", back_populates="shows")
    scenario = relationship("Scenario", back_populates="shows")
    tickets = relationship("Ticket", back_populates="show")
    votes_vip = relationship("Vote_VIP", back_populates="show")
    rented_equipment = relationship("Rent_Equipment", back_populates="show")
    rented_services = relationship("Rent_Service", back_populates="show")

    __table_args__ = (CheckConstraint(vote_type.in_(['common', 'vip', 'both']), name='chk_vote_type'),)


class Customer(Base):
    __tablename__ = "Customer"

    email = Column(String(100), primary_key=True, index=True)
    phone = Column(String(20))
    password = Column(String(128), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())

    # Связи
    tickets = relationship("Ticket", back_populates="customer")


class Ticket(Base):
    __tablename__ = "Ticket"

    ticket_id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer)  # BIGINT
    show_id = Column(Integer, ForeignKey("Show.show_id"))
    seat_number = Column(String(20))
    price = Column(Numeric(10, 2))  # NUMERIC(10, 2)
    status = Column(String(50))  # CHECK (status IN ('available', 'booked', 'sold', 'registered'))
    vip_status = Column(Boolean, default=False)
    email = Column(String(100), ForeignKey("Customer.email"))

    # Связи
    show = relationship("Show", back_populates="tickets")
    customer = relationship("Customer", back_populates="tickets")
    votes_common = relationship("Vote_Common", back_populates="ticket")
    votes_vip = relationship("Vote_VIP", back_populates="ticket")

    __table_args__ = (CheckConstraint(status.in_(['available', 'booked', 'sold', 'registered']), name='chk_ticket_status'),)


class Vote_Common(Base):
    __tablename__ = "Vote_Common"

    ticket_id = Column(Integer, ForeignKey("Ticket.ticket_id"), primary_key=True)
    vote_id = Column(Integer, primary_key=True, index=True)
    value = Column(String(50))

    # Связи
    ticket = relationship("Ticket", back_populates="votes_common")


class Vote_VIP(Base):
    __tablename__ = "Vote_VIP"

    vote_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("Ticket.ticket_id"))
    show_id = Column(Integer, ForeignKey("Show.show_id"))
    act_id = Column(Integer, ForeignKey("Act.id"))
    value = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    # Связи
    ticket = relationship("Ticket", back_populates="votes_vip")
    show = relationship("Show", back_populates="votes_vip")
    act = relationship("Act", back_populates="votes_vip")


class Equipment(Base):
    __tablename__ = "Equipment"

    equipment_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    price = Column(Numeric(10, 2))  # NUMERIC(10, 2)
    amount = Column(Integer)

    # Связи
    rented_equipment = relationship("Rent_Equipment", back_populates="equipment")


class Rent_Equipment(Base):
    __tablename__ = "Rent_Equipment"

    equipment_id = Column(Integer, ForeignKey("Equipment.equipment_id"), primary_key=True)
    show_id = Column(Integer, ForeignKey("Show.show_id"), primary_key=True)
    rent_start = Column(DateTime)
    rent_end = Column(DateTime)

    # Связи
    equipment = relationship("Equipment", back_populates="rented_equipment")
    show = relationship("Show", back_populates="rented_equipment")


class Service(Base):
    __tablename__ = "Service"

    service_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    price = Column(Numeric(10, 2))  # NUMERIC(10, 2)
    amount = Column(Integer)

    # Связи
    rented_services = relationship("Rent_Service", back_populates="service")


class Rent_Service(Base):
    __tablename__ = "Rent_Service"

    service_id = Column(Integer, ForeignKey("Service.service_id"), primary_key=True)
    show_id = Column(Integer, ForeignKey("Show.show_id"), primary_key=True)
    rent_start = Column(DateTime)
    rent_end = Column(DateTime)

    # Связи
    service = relationship("Service", back_populates="rented_services")
    show = relationship("Show", back_populates="rented_services")