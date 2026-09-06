from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from decimal import Decimal

from app.roles import ALL_ROLES


# Схемы для Employee
class EmployeeBase(BaseModel):
    username: str
    role: str

    @field_validator("role")
    @classmethod
    def role_known(cls, v: str) -> str:
        s = (v or "").strip()
        if s not in ALL_ROLES:
            raise ValueError(f"role must be one of: {', '.join(sorted(ALL_ROLES))}")
        return s


class EmployeeCreate(EmployeeBase):
    password: str


class EmployeeUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

    @field_validator("role")
    @classmethod
    def role_known_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        s = v.strip()
        if s not in ALL_ROLES:
            raise ValueError(f"role must be one of: {', '.join(sorted(ALL_ROLES))}")
        return s


class Employee(EmployeeBase):
    id: int
    last_online: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для Franchise
class FranchiseBase(BaseModel):
    contact_person: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    royalty_percentage: Optional[Decimal] = None
    initial_fee: Optional[Decimal] = None
    monthly_fee: Optional[Decimal] = None


class FranchiseCreate(FranchiseBase):
    pass


class Franchise(FranchiseBase):
    contract_id: int

    class Config:
        from_attributes = True


# Схемы для Theater
class TheaterBase(BaseModel):
    contract_id: int
    name: Optional[str] = None
    location: Optional[str] = None


class TheaterCreate(TheaterBase):
    pass


class Theater(TheaterBase):
    theater_id: int

    class Config:
        from_attributes = True


# Схемы для Hall
class HallBase(BaseModel):
    theater_id: int
    capacity: Optional[int] = None


class HallCreate(HallBase):
    pass


class Hall(HallBase):
    hall_id: int

    class Config:
        from_attributes = True


# Схемы для Scenario
class ScenarioBase(BaseModel):
    title: str
    status: Optional[str] = None
    description: Optional[str] = None


class ScenarioCreate(ScenarioBase):
    pass


class Scenario(ScenarioBase):
    scenario_id: int
    created_at: Optional[datetime] = None
    tz_source_filename: Optional[str] = None
    tz_result_filename: Optional[str] = None
    tz_pipeline_status: Optional[str] = None

    class Config:
        from_attributes = True


# Схемы для Act
class ActBase(BaseModel):
    scenario_id: int
    title: str
    position: int


class ActCreate(ActBase):
    pass


class Act(ActBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для Part
class PartBase(BaseModel):
    act_id: int
    title: str
    file_path: str
    position: int


class PartCreate(PartBase):
    pass


class Part(PartBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для Show
class ShowBase(BaseModel):
    hall_id: int
    scenario_id: Optional[int] = None
    title: Optional[str] = None
    vote_type: Optional[str] = None  # 'common', 'vip', 'both'
    duration: Optional[str] = None  # INTERVAL
    show_date: Optional[datetime] = None


class ShowCreate(ShowBase):
    pass


class Show(ShowBase):
    show_id: int

    class Config:
        from_attributes = True


# Схемы для Customer
class CustomerBase(BaseModel):
    phone: Optional[str] = None


class CustomerCreate(CustomerBase):
    email: str


class Customer(CustomerBase):
    email: str

    class Config:
        from_attributes = True


class PublicCustomerRegister(BaseModel):
    email: str
    phone: Optional[str] = None
    password: str


class PublicCustomerLogin(BaseModel):
    email: str
    password: str


class PublicCustomerMe(BaseModel):
    email: str
    phone: Optional[str] = None
    is_active: bool


class PublicSeat(BaseModel):
    ticket_id: int
    seat_number: Optional[str] = None
    status: Optional[str] = None
    price: Optional[Decimal] = None
    vip_status: Optional[bool] = None


class PublicReservationCreate(BaseModel):
    show_id: int
    seat_number: str


# Схемы для Ticket
class TicketBase(BaseModel):
    owner_id: Optional[int] = None
    show_id: int
    seat_number: Optional[str] = None
    price: Optional[Decimal] = None
    status: Optional[str] = None  # 'available', 'booked', 'sold', 'registered'
    vip_status: Optional[bool] = None


class TicketCreate(TicketBase):
    email: str


class Ticket(TicketBase):
    ticket_id: int

    class Config:
        from_attributes = True


# Схемы для Vote_Common
class VoteCommonBase(BaseModel):
    ticket_id: int
    value: str


class VoteCommonCreate(VoteCommonBase):
    pass


class VoteCommon(VoteCommonBase):
    vote_id: int

    class Config:
        from_attributes = True


# Схемы для Vote_VIP
class VoteVIPBase(BaseModel):
    ticket_id: int
    show_id: int
    act_id: int
    value: str


class VoteVIPCreate(VoteVIPBase):
    pass


class VoteVIP(VoteVIPBase):
    vote_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для Equipment
class EquipmentBase(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    amount: Optional[int] = None


class EquipmentCreate(EquipmentBase):
    pass


class Equipment(EquipmentBase):
    equipment_id: int

    class Config:
        from_attributes = True


# Схемы для Rent_Equipment
class RentEquipmentBase(BaseModel):
    equipment_id: int
    show_id: int
    rent_start: Optional[datetime] = None
    rent_end: Optional[datetime] = None


class RentEquipmentCreate(RentEquipmentBase):
    pass


class RentEquipment(RentEquipmentBase):
    class Config:
        from_attributes = True


# Схемы для Service
class ServiceBase(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    amount: Optional[int] = None


class ServiceCreate(ServiceBase):
    pass


class Service(ServiceBase):
    service_id: int

    class Config:
        from_attributes = True


# Схемы для Rent_Service
class RentServiceBase(BaseModel):
    service_id: int
    show_id: int
    rent_start: Optional[datetime] = None
    rent_end: Optional[datetime] = None


class RentServiceCreate(RentServiceBase):
    pass


class RentService(RentServiceBase):
    class Config:
        from_attributes = True