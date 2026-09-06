import logging
import re
import uuid
from pathlib import Path

import requests
from fastapi import FastAPI, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Any, List
from fastapi.security import OAuth2PasswordRequestForm

logger = logging.getLogger(__name__)

from app.roles import (
    ALL_ROLES,
    PERMISSION_KEYS,
    ROLE_ADMIN,
    PERMISSION_CONTENT_WRITE,
    PERMISSION_EMPLOYEE_MANAGE,
    PERMISSION_EMPLOYEE_READ,
    PERMISSION_FRANCHISE_WRITE,
    PERMISSION_OPERATIONAL_WRITE,
    PERMISSION_VOTE_WRITE,
)

from . import config as api_config
from . import crud, models, schemas, scenario_files
from .database import engine, get_db
from .auth import create_access_token, authenticate_user
from .rbac import require_any_authenticated_user, require_permission, require_roles
from .public_api import router as public_router

def _ensure_customer_auth_columns() -> None:
    """Idempotent hotfix for public auth columns in existing databases."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE "Customer"
                ADD COLUMN IF NOT EXISTS password VARCHAR(128),
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
                """
            )
        )


models.Base.metadata.create_all(bind=engine)
_ensure_customer_auth_columns()

app = FastAPI(title="Theater Management System API", version="1.0.0")
app.include_router(public_router)


@app.exception_handler(SQLAlchemyError)
async def _sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Понятная ошибка при рассинхроне модели и БД (например, не применена миграция ТЗ)."""
    logger.exception("Ошибка SQLAlchemy при %s %s", request.method, request.url.path)
    raw = ""
    try:
        raw = str(getattr(exc, "orig", exc) or exc)
    except Exception:
        raw = str(exc)
    low = raw.lower()
    hint = ""
    if "tz_source" in low or "tz_result" in low or "tz_pipeline" in low or "undefinedcolumn" in low.replace(
        " ", ""
    ):
        hint = (
            " Похоже, не применена миграция колонок ТЗ: из корня проекта выполните "
            "`python scripts/apply_scenario_tz_migration.py` (или SQL из migrations/add_scenario_tz_columns.sql), "
            "затем перезапустите API."
        )
    elif 'relation "scenario"' in low or 'relation "Scenario"' in low:
        hint = " Проверьте, что имя таблицы сценариев в БД совпадает с тем, что ожидает SQLAlchemy (см. миграцию)."
    return JSONResponse(
        status_code=500,
        content={"detail": f"Ошибка базы данных.{hint} Технически: {raw[:400]}"},
    )


# --- Зависимости: права из матрицы RolePermission + статические умолчания ---
_req_employee_rw = require_permission(PERMISSION_EMPLOYEE_READ)
_req_employee_admin = require_permission(PERMISSION_EMPLOYEE_MANAGE)
_req_franchise_write = require_permission(PERMISSION_FRANCHISE_WRITE)
_req_operational_write = require_permission(PERMISSION_OPERATIONAL_WRITE)
_req_content_write = require_permission(PERMISSION_CONTENT_WRITE)
_req_vote_write = require_permission(PERMISSION_VOTE_WRITE)


@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.Employee)
async def read_users_me(current_user: models.Employee = Depends(require_any_authenticated_user)):
    return current_user


@app.get("/role-permissions")
def read_role_permissions(
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
) -> dict[str, dict[str, bool]]:
    """Текущая матрица прав (для интерфейса и клиента)."""
    return crud.get_full_role_permissions_matrix(db)


@app.put("/role-permissions")
def write_role_permissions(
    body: dict[str, dict[str, Any]],
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_roles("admin")),
) -> dict[str, dict[str, bool]]:
    """Изменение прав по ролям (только учётная запись с ролью admin в JWT)."""
    for role, row in body.items():
        r = (role or "").strip()
        if r not in ALL_ROLES or r == ROLE_ADMIN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недопустимая роль: {role!r}")
        if not isinstance(row, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для каждой роли ожидается объект прав")
        for k in row:
            if k not in PERMISSION_KEYS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неизвестный ключ права: {k!r}",
                )
    normalized: dict[str, dict[str, bool]] = {}
    for role, row in body.items():
        r = (role or "").strip()
        if r in ALL_ROLES and r != ROLE_ADMIN:
            normalized[r] = {k: bool(row[k]) for k in row}
    crud.replace_role_permissions_matrix(db, normalized)
    return crud.get_full_role_permissions_matrix(db)


# CRUD для Employee
@app.get("/employees/", response_model=List[schemas.Employee])
def read_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_employee_rw),
):
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees


@app.get("/employees/{employee_id}", response_model=schemas.Employee)
def read_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_employee_rw),
):
    employee = crud.get_employee(db, employee_id=employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.post("/employees/", response_model=schemas.Employee)
def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_employee_admin),
):
    return crud.create_employee(db=db, employee=employee)


@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_employee_admin),
):
    success = crud.delete_employee(db=db, employee_id=employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}


@app.put("/employees/{employee_id}", response_model=schemas.Employee)
def update_employee(
    employee_id: int,
    employee: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_employee_admin),
):
    updated_employee = crud.update_employee(db=db, employee_id=employee_id, employee=employee)
    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_employee


# CRUD для Franchise
@app.get("/franchises/", response_model=List[schemas.Franchise])
def read_franchises(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    franchises = crud.get_franchises(db, skip=skip, limit=limit)
    return franchises


@app.get("/franchises/{franchise_id}", response_model=schemas.Franchise)
def read_franchise(
    franchise_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    franchise = crud.get_franchise(db, franchise_id=franchise_id)
    if franchise is None:
        raise HTTPException(status_code=404, detail="Franchise not found")
    return franchise


@app.post("/franchises/", response_model=schemas.Franchise)
def create_franchise(
    franchise: schemas.FranchiseCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_franchise_write),
):
    return crud.create_franchise(db=db, franchise=franchise)


@app.put("/franchises/{franchise_id}", response_model=schemas.Franchise)
def update_franchise(
    franchise_id: int,
    franchise: schemas.FranchiseCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_franchise_write),
):
    updated_franchise = crud.update_franchise(db=db, franchise_id=franchise_id, franchise=franchise)
    if updated_franchise is None:
        raise HTTPException(status_code=404, detail="Franchise not found")
    return updated_franchise


@app.delete("/franchises/{franchise_id}")
def delete_franchise(
    franchise_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_franchise_write),
):
    success = crud.delete_franchise(db=db, franchise_id=franchise_id)
    if not success:
        raise HTTPException(status_code=404, detail="Franchise not found")
    return {"message": "Franchise deleted successfully"}


# CRUD для Theater
@app.get("/theaters/", response_model=List[schemas.Theater])
def read_theaters(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    theaters = crud.get_theaters(db, skip=skip, limit=limit)
    return theaters


@app.get("/theaters/{theater_id}", response_model=schemas.Theater)
def read_theater(
    theater_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    theater = crud.get_theater(db, theater_id=theater_id)
    if theater is None:
        raise HTTPException(status_code=404, detail="Theater not found")
    return theater


@app.post("/theaters/", response_model=schemas.Theater)
def create_theater(
    theater: schemas.TheaterCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_theater(db=db, theater=theater)


@app.put("/theaters/{theater_id}", response_model=schemas.Theater)
def update_theater(
    theater_id: int,
    theater: schemas.TheaterCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    updated = crud.update_theater(db=db, theater_id=theater_id, theater=theater)
    if updated is None:
        raise HTTPException(status_code=404, detail="Theater not found")
    return updated


@app.delete("/theaters/{theater_id}")
def delete_theater(
    theater_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_theater(db=db, theater_id=theater_id)
    if not success:
        raise HTTPException(status_code=404, detail="Theater not found")
    return {"message": "Theater deleted successfully"}


# CRUD для Hall
@app.get("/halls/", response_model=List[schemas.Hall])
def read_halls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    halls = crud.get_halls(db, skip=skip, limit=limit)
    return halls


@app.get("/halls/{hall_id}", response_model=schemas.Hall)
def read_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    hall = crud.get_hall(db, hall_id=hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")
    return hall


@app.post("/halls/", response_model=schemas.Hall)
def create_hall(
    hall: schemas.HallCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_hall(db=db, hall=hall)


@app.put("/halls/{hall_id}", response_model=schemas.Hall)
def update_hall(
    hall_id: int,
    hall: schemas.HallCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    updated = crud.update_hall(db=db, hall_id=hall_id, hall=hall)
    if updated is None:
        raise HTTPException(status_code=404, detail="Hall not found")
    return updated


@app.delete("/halls/{hall_id}")
def delete_hall(
    hall_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_hall(db=db, hall_id=hall_id)
    if not success:
        raise HTTPException(status_code=404, detail="Hall not found")
    return {"message": "Hall deleted successfully"}


# CRUD для Scenario
@app.get("/scenarios/", response_model=List[schemas.Scenario])
def read_scenarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    scenarios = crud.get_scenarios(db, skip=skip, limit=limit)
    return scenarios


@app.get("/scenarios/{scenario_id}", response_model=schemas.Scenario)
def read_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    scenario = crud.get_scenario(db, scenario_id=scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@app.post("/scenarios/", response_model=schemas.Scenario)
def create_scenario(
    scenario: schemas.ScenarioCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    return crud.create_scenario(db=db, scenario=scenario)


@app.delete("/scenarios/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    success = crud.delete_scenario(db=db, scenario_id=scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"message": "Scenario deleted successfully"}


def _filename_from_content_disposition(cd: str) -> str | None:
    if not cd:
        return None
    m = re.search(r"filename\*=UTF-8''([^;\s]+)", cd, re.I)
    if m:
        from urllib.parse import unquote

        return unquote(m.group(1).strip())
    m = re.search(r'filename="([^"]+)"', cd)
    if m:
        return m.group(1).strip()
    m = re.search(r"filename=([^;\s]+)", cd, re.I)
    return m.group(1).strip() if m else None


@app.post("/scenarios/{scenario_id}/tz-spec/upload", response_model=schemas.Scenario)
async def upload_scenario_tz_spec(
    scenario_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    """Загрузка файла ТЗ (текст/документ) для сценария."""
    sc = crud.get_scenario(db, scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in scenario_files.ALLOWED_TZ_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Допустимые расширения: {', '.join(sorted(scenario_files.ALLOWED_TZ_SUFFIXES))}",
        )
    data = await file.read()
    if len(data) > scenario_files.MAX_TZ_BYTES:
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 25 МБ)")
    rel_dir = scenario_files.scenario_rel_prefix(scenario_id)
    inner = f"{uuid.uuid4().hex}{suffix}"
    relpath = f"{rel_dir}/{inner}"
    dest = scenario_files.safe_resolve(relpath)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    orig = scenario_files.sanitize_original_filename(file.filename or "tz")
    updated = crud.attach_scenario_tz_source(db, scenario_id, orig, relpath)
    return updated


@app.get("/scenarios/{scenario_id}/tz-spec/download")
def download_scenario_tz_spec(
    scenario_id: int,
    kind: str = Query("source", description="source или result"),
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    if kind not in ("source", "result"):
        raise HTTPException(status_code=400, detail="kind должен быть source или result")
    sc = crud.get_scenario(db, scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    relpath = sc.tz_source_relpath if kind == "source" else sc.tz_result_relpath
    fname = sc.tz_source_filename if kind == "source" else sc.tz_result_filename
    if not relpath:
        raise HTTPException(status_code=404, detail="Файл не приложен")
    full = scenario_files.safe_resolve(relpath)
    if not full.is_file():
        raise HTTPException(status_code=404, detail="Файл отсутствует на сервере")
    return FileResponse(
        path=str(full),
        filename=fname or ("tz" + Path(relpath).suffix),
        media_type="application/octet-stream",
    )


@app.post("/scenarios/{scenario_id}/tz-spec/process", response_model=schemas.Scenario)
def process_scenario_tz_via_n8n(
    scenario_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    """
    Отправляет загруженный ТЗ-файл в n8n (вебхук) и сохраняет тело ответа как результат.
    Переменная окружения N8N_TZ_WEBHOOK_URL должна указывать на POST webhook.
    """
    if not api_config.N8N_TZ_WEBHOOK_URL:
        raise HTTPException(
            status_code=400,
            detail="Обработка не настроена: задайте N8N_TZ_WEBHOOK_URL на сервере API.",
        )
    sc = crud.get_scenario(db, scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not sc.tz_source_relpath:
        raise HTTPException(status_code=400, detail="Сначала загрузите файл ТЗ")
    src_path = scenario_files.safe_resolve(sc.tz_source_relpath)
    if not src_path.is_file():
        raise HTTPException(status_code=400, detail="Исходный файл не найден на сервере")

    crud.set_scenario_tz_pipeline_status(db, scenario_id, "pending")
    try:
        with open(src_path, "rb") as fh:
            r = requests.post(
                api_config.N8N_TZ_WEBHOOK_URL,
                files={
                    "file": (
                        sc.tz_source_filename or "tz",
                        fh,
                        "application/octet-stream",
                    )
                },
                timeout=api_config.N8N_TZ_TIMEOUT_SEC,
            )
    except requests.RequestException as e:
        crud.set_scenario_tz_pipeline_status(db, scenario_id, "error")
        raise HTTPException(status_code=502, detail=f"Ошибка вызова n8n: {e}") from e

    if r.status_code >= 400:
        crud.set_scenario_tz_pipeline_status(db, scenario_id, "error")
        raise HTTPException(status_code=502, detail=f"n8n вернул HTTP {r.status_code}")

    if not r.content:
        crud.set_scenario_tz_pipeline_status(db, scenario_id, "error")
        raise HTTPException(status_code=502, detail="Пустой ответ от n8n")

    result_name = _filename_from_content_disposition(r.headers.get("Content-Disposition", ""))
    if not result_name:
        ct = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        ext = ".bin"
        if "pdf" in ct:
            ext = ".pdf"
        elif "word" in ct or "docx" in ct:
            ext = ".docx"
        elif "text" in ct or "plain" in ct:
            ext = ".txt"
        result_name = f"tz_processed{ext}"

    result_name = scenario_files.sanitize_original_filename(result_name)
    rel_dir = scenario_files.scenario_rel_prefix(scenario_id)
    inner = f"result_{uuid.uuid4().hex}{Path(result_name).suffix or '.bin'}"
    relpath = f"{rel_dir}/{inner}"
    dest = scenario_files.safe_resolve(relpath)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    updated = crud.attach_scenario_tz_result(db, scenario_id, result_name, relpath, "ready")
    if updated is None:
        raise HTTPException(status_code=500, detail="Не удалось сохранить результат")
    return updated


# CRUD для Act
@app.get("/acts/", response_model=List[schemas.Act])
def read_acts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    acts = crud.get_acts(db, skip=skip, limit=limit)
    return acts


@app.get("/acts/{act_id}", response_model=schemas.Act)
def read_act(
    act_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    act = crud.get_act(db, act_id=act_id)
    if act is None:
        raise HTTPException(status_code=404, detail="Act not found")
    return act


@app.post("/acts/", response_model=schemas.Act)
def create_act(
    act: schemas.ActCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    return crud.create_act(db=db, act=act)


@app.delete("/acts/{act_id}")
def delete_act(
    act_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    success = crud.delete_act(db=db, act_id=act_id)
    if not success:
        raise HTTPException(status_code=404, detail="Act not found")
    return {"message": "Act deleted successfully"}


# CRUD для Part
@app.get("/parts/", response_model=List[schemas.Part])
def read_parts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    parts = crud.get_parts(db, skip=skip, limit=limit)
    return parts


@app.get("/parts/{part_id}", response_model=schemas.Part)
def read_part(
    part_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    part = crud.get_part(db, part_id=part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@app.post("/parts/", response_model=schemas.Part)
def create_part(
    part: schemas.PartCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    return crud.create_part(db=db, part=part)


@app.delete("/parts/{part_id}")
def delete_part(
    part_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_content_write),
):
    success = crud.delete_part(db=db, part_id=part_id)
    if not success:
        raise HTTPException(status_code=404, detail="Part not found")
    return {"message": "Part deleted successfully"}


# CRUD для Show
@app.get("/shows/", response_model=List[schemas.Show])
def read_shows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    shows = crud.get_shows(db, skip=skip, limit=limit)
    return shows


@app.get("/shows/{show_id}", response_model=schemas.Show)
def read_show(
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    show = crud.get_show(db, show_id=show_id)
    if show is None:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


@app.post("/shows/", response_model=schemas.Show)
def create_show(
    show: schemas.ShowCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_show(db=db, show=show)


@app.put("/shows/{show_id}", response_model=schemas.Show)
def update_show(
    show_id: int,
    show: schemas.ShowCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    updated = crud.update_show(db=db, show_id=show_id, show=show)
    if updated is None:
        raise HTTPException(status_code=404, detail="Show not found")
    return updated


@app.delete("/shows/{show_id}")
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_show(db=db, show_id=show_id)
    if not success:
        raise HTTPException(status_code=404, detail="Show not found")
    return {"message": "Show deleted successfully"}


# CRUD для Customer
@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    customers = crud.get_customers(db, skip=skip, limit=limit)
    return customers


@app.get("/customers/{email}", response_model=schemas.Customer)
def read_customer(
    email: str,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    customer = crud.get_customer(db, email=email)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.post("/customers/", response_model=schemas.Customer)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_customer(db=db, customer=customer)


@app.delete("/customers/{email}")
def delete_customer(
    email: str,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_customer(db=db, email=email)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}


# CRUD для Ticket
@app.get("/tickets/", response_model=List[schemas.Ticket])
def read_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    tickets = crud.get_tickets(db, skip=skip, limit=limit)
    return tickets


@app.get("/tickets/{ticket_id}", response_model=schemas.Ticket)
def read_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/tickets/", response_model=schemas.Ticket)
def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_ticket(db=db, ticket=ticket)


@app.put("/tickets/{ticket_id}", response_model=schemas.Ticket)
def update_ticket(
    ticket_id: int,
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    updated = crud.update_ticket(db=db, ticket_id=ticket_id, ticket=ticket)
    if updated is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated


@app.delete("/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_ticket(db=db, ticket_id=ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully"}


# CRUD для Vote_Common
@app.get("/votes_common/", response_model=List[schemas.VoteCommon])
def read_votes_common(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    votes = crud.get_votes_common(db, skip=skip, limit=limit)
    return votes


@app.get("/votes_common/{ticket_id}/{vote_id}", response_model=schemas.VoteCommon)
def read_vote_common(
    ticket_id: int,
    vote_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    vote = crud.get_vote_common(db, ticket_id=ticket_id, vote_id=vote_id)
    if vote is None:
        raise HTTPException(status_code=404, detail="Vote Common not found")
    return vote


@app.post("/votes_common/", response_model=schemas.VoteCommon)
def create_vote_common(
    vote: schemas.VoteCommonCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_vote_write),
):
    return crud.create_vote_common(db=db, vote_common=vote)


@app.delete("/votes_common/{ticket_id}/{vote_id}")
def delete_vote_common(
    ticket_id: int,
    vote_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_vote_write),
):
    success = crud.delete_vote_common(db=db, ticket_id=ticket_id, vote_id=vote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vote Common not found")
    return {"message": "Vote Common deleted successfully"}


# CRUD для Vote_VIP
@app.get("/votes_vip/", response_model=List[schemas.VoteVIP])
def read_votes_vip(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    votes = crud.get_votes_vip(db, skip=skip, limit=limit)
    return votes


@app.get("/votes_vip/{vote_id}", response_model=schemas.VoteVIP)
def read_vote_vip(
    vote_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    vote = crud.get_vote_vip(db, vote_id=vote_id)
    if vote is None:
        raise HTTPException(status_code=404, detail="Vote VIP not found")
    return vote


@app.post("/votes_vip/", response_model=schemas.VoteVIP)
def create_vote_vip(
    vote: schemas.VoteVIPCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_vote_write),
):
    return crud.create_vote_vip(db=db, vote_vip=vote)


@app.delete("/votes_vip/{vote_id}")
def delete_vote_vip(
    vote_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_vote_write),
):
    success = crud.delete_vote_vip(db=db, vote_id=vote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vote VIP not found")
    return {"message": "Vote VIP deleted successfully"}


# CRUD для Equipment
@app.get("/equipments/", response_model=List[schemas.Equipment])
def read_equipments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    equipments = crud.get_equipments(db, skip=skip, limit=limit)
    return equipments


@app.get("/equipments/{equipment_id}", response_model=schemas.Equipment)
def read_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    equipment = crud.get_equipment(db, equipment_id=equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@app.post("/equipments/", response_model=schemas.Equipment)
def create_equipment(
    equipment: schemas.EquipmentCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_equipment(db=db, equipment=equipment)


@app.delete("/equipments/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_equipment(db=db, equipment_id=equipment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}


# CRUD для Rent_Equipment
@app.get("/rents_equipment/", response_model=List[schemas.RentEquipment])
def read_rents_equipment(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    rents = crud.get_rents_equipment(db, skip=skip, limit=limit)
    return rents


@app.get("/rents_equipment/{equipment_id}/{show_id}", response_model=schemas.RentEquipment)
def read_rent_equipment(
    equipment_id: int,
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    rent = crud.get_rent_equipment(db, equipment_id=equipment_id, show_id=show_id)
    if rent is None:
        raise HTTPException(status_code=404, detail="Rent Equipment not found")
    return rent


@app.post("/rents_equipment/", response_model=schemas.RentEquipment)
def create_rent_equipment(
    rent: schemas.RentEquipmentCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_rent_equipment(db=db, rent_equipment=rent)


@app.delete("/rents_equipment/{equipment_id}/{show_id}")
def delete_rent_equipment(
    equipment_id: int,
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_rent_equipment(db=db, equipment_id=equipment_id, show_id=show_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rent Equipment not found")
    return {"message": "Rent Equipment deleted successfully"}


# CRUD для Service
@app.get("/services/", response_model=List[schemas.Service])
def read_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    services = crud.get_services(db, skip=skip, limit=limit)
    return services


@app.get("/services/{service_id}", response_model=schemas.Service)
def read_service(
    service_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    service = crud.get_service(db, service_id=service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@app.post("/services/", response_model=schemas.Service)
def create_service(
    service: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_service(db=db, service=service)


@app.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_service(db=db, service_id=service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted successfully"}


# CRUD для Rent_Service
@app.get("/rents_service/", response_model=List[schemas.RentService])
def read_rents_service(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    rents = crud.get_rents_service(db, skip=skip, limit=limit)
    return rents


@app.get("/rents_service/{service_id}/{show_id}", response_model=schemas.RentService)
def read_rent_service(
    service_id: int,
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(require_any_authenticated_user),
):
    rent = crud.get_rent_service(db, service_id=service_id, show_id=show_id)
    if rent is None:
        raise HTTPException(status_code=404, detail="Rent Service not found")
    return rent


@app.post("/rents_service/", response_model=schemas.RentService)
def create_rent_service(
    rent: schemas.RentServiceCreate,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    return crud.create_rent_service(db=db, rent_service=rent)


@app.delete("/rents_service/{service_id}/{show_id}")
def delete_rent_service(
    service_id: int,
    show_id: int,
    db: Session = Depends(get_db),
    _u: models.Employee = Depends(_req_operational_write),
):
    success = crud.delete_rent_service(db=db, service_id=service_id, show_id=show_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rent Service not found")
    return {"message": "Rent Service deleted successfully"}
