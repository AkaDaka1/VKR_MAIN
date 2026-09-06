from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .auth import authenticate_customer, create_access_token, get_current_customer
from .database import get_db

router = APIRouter(prefix="/public/v1", tags=["public"])


@router.post("/auth/register", response_model=schemas.PublicCustomerMe)
async def register_customer(
    payload: schemas.PublicCustomerRegister,
    db: Session = Depends(get_db),
):
    existing = crud.get_customer_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    customer = crud.create_customer_account(db, payload)
    return schemas.PublicCustomerMe(email=customer.email, phone=customer.phone, is_active=bool(customer.is_active))


@router.post("/auth/login", response_model=dict)
async def login_customer(
    payload: schemas.PublicCustomerLogin,
    db: Session = Depends(get_db),
):
    customer = await authenticate_customer(payload.email, payload.password, db)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": customer.email, "kind": "customer"})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.PublicCustomerMe)
async def read_me(current_customer: models.Customer = Depends(get_current_customer)):
    return schemas.PublicCustomerMe(
        email=current_customer.email,
        phone=current_customer.phone,
        is_active=bool(current_customer.is_active),
    )


@router.get("/theaters", response_model=List[schemas.Theater])
async def list_theaters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.get_theaters(db, skip=skip, limit=limit)


@router.get("/theaters/{theater_id}/shows", response_model=List[schemas.Show])
async def list_theater_shows(
    theater_id: int,
    show_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Show)
        .join(models.Hall, models.Hall.hall_id == models.Show.hall_id)
        .filter(models.Hall.theater_id == theater_id)
    )
    if show_date:
        start = datetime.combine(show_date, time.min)
        end = datetime.combine(show_date, time.max)
        query = query.filter(models.Show.show_date >= start, models.Show.show_date <= end)
    return query.order_by(models.Show.show_date.asc()).all()


@router.get("/shows/{show_id}/seats", response_model=List[schemas.PublicSeat])
async def list_show_seats(
    show_id: int,
    db: Session = Depends(get_db),
):
    tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.show_id == show_id)
        .order_by(models.Ticket.seat_number.asc())
        .all()
    )
    return [
        schemas.PublicSeat(
            ticket_id=t.ticket_id,
            seat_number=t.seat_number,
            status=t.status,
            price=t.price,
            vip_status=t.vip_status,
        )
        for t in tickets
    ]


@router.post("/reservations", response_model=schemas.Ticket)
async def reserve_ticket(
    payload: schemas.PublicReservationCreate,
    db: Session = Depends(get_db),
    customer: models.Customer = Depends(get_current_customer),
):
    reserved = crud.reserve_ticket_for_customer(
        db=db,
        show_id=payload.show_id,
        seat_number=payload.seat_number,
        customer_email=customer.email,
    )
    if not reserved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Seat is not available")
    return reserved


@router.get("/reservations/my", response_model=List[schemas.Ticket])
async def my_reservations(
    db: Session = Depends(get_db),
    customer: models.Customer = Depends(get_current_customer),
):
    return crud.get_customer_reservations(db, customer.email)
