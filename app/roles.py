"""
Каталог ролей и прав доступа (общий для клиента и документации).

Слаги ролей хранятся в БД (Employee.role) в нижнем регистре на латинице.
Права по ключам синхронизируются с API (таблица RolePermission); до загрузки
матрицы с сервера используются статические значения по умолчанию.
"""
from __future__ import annotations

from copy import deepcopy
from typing import FrozenSet

ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_SCENARIST = "scenarist"
ROLE_FRANCHISE_PARTNER = "franchise_partner"
ROLE_USER = "user"

ALL_ROLES: FrozenSet[str] = frozenset(
    {
        ROLE_ADMIN,
        ROLE_MANAGER,
        ROLE_SCENARIST,
        ROLE_FRANCHISE_PARTNER,
        ROLE_USER,
    }
)

ROLE_LABELS_RU: dict[str, str] = {
    ROLE_ADMIN: "Администратор",
    ROLE_MANAGER: "Менеджер",
    ROLE_SCENARIST: "Сценарист",
    ROLE_FRANCHISE_PARTNER: "Партнёр по франшизе",
    ROLE_USER: "Пользователь",
}

ROLE_COMBO_OPTIONS: list[tuple[str, str]] = [(ROLE_LABELS_RU[r], r) for r in sorted(ALL_ROLES)]

# Ключи прав (сервер и клиент)
PERMISSION_EMPLOYEE_READ = "employee_read"
PERMISSION_EMPLOYEE_MANAGE = "employee_manage"
PERMISSION_FRANCHISE_WRITE = "franchise_write"
PERMISSION_OPERATIONAL_WRITE = "operational_write"
PERMISSION_CONTENT_WRITE = "content_write"
PERMISSION_VOTE_WRITE = "vote_write"
PERMISSION_VIEW_DASHBOARD = "view_dashboard"

PERMISSION_KEYS: tuple[str, ...] = (
    PERMISSION_EMPLOYEE_READ,
    PERMISSION_EMPLOYEE_MANAGE,
    PERMISSION_FRANCHISE_WRITE,
    PERMISSION_OPERATIONAL_WRITE,
    PERMISSION_CONTENT_WRITE,
    PERMISSION_VOTE_WRITE,
    PERMISSION_VIEW_DASHBOARD,
)

PERMISSION_LABELS_RU: dict[str, str] = {
    PERMISSION_EMPLOYEE_READ: "Просмотр списка сотрудников",
    PERMISSION_EMPLOYEE_MANAGE: "Управление учётными записями (создание, правка, удаление)",
    PERMISSION_FRANCHISE_WRITE: "Изменение франшиз",
    PERMISSION_OPERATIONAL_WRITE: "Операционные данные (театры, залы, показы, билеты, …)",
    PERMISSION_CONTENT_WRITE: "Контент (сценарии, акты, части)",
    PERMISSION_VOTE_WRITE: "Голосования",
    PERMISSION_VIEW_DASHBOARD: "Дашборд (сводная статистика)",
}

# Матрица с сервера GET /role-permissions (полная по ролям); None — только статические умолчания
_live_permissions: dict[str, dict[str, bool]] | None = None


def normalize_role(role: str | None) -> str:
    return (role or "").strip()


def is_known_role(role: str | None) -> bool:
    return normalize_role(role) in ALL_ROLES


def static_permission_row(role: str | None) -> dict[str, bool]:
    """Статические умолчания (как до настраиваемых прав в БД)."""
    r = normalize_role(role)
    base = {k: False for k in PERMISSION_KEYS}
    if r == ROLE_ADMIN:
        return {k: True for k in PERMISSION_KEYS}
    if r == ROLE_MANAGER:
        base[PERMISSION_EMPLOYEE_READ] = True
        base[PERMISSION_FRANCHISE_WRITE] = True
        base[PERMISSION_OPERATIONAL_WRITE] = True
        base[PERMISSION_CONTENT_WRITE] = True
        base[PERMISSION_VOTE_WRITE] = True
        return base
    if r == ROLE_SCENARIST:
        base[PERMISSION_CONTENT_WRITE] = True
        return base
    return base


def set_role_permissions_matrix(matrix: dict[str, dict[str, bool]] | None) -> None:
    """Установить полную матрицу прав с API или сбросить на статические умолчания."""
    global _live_permissions
    if matrix is None:
        _live_permissions = None
        return
    out: dict[str, dict[str, bool]] = {}
    for role, row in matrix.items():
        r = normalize_role(role)
        if not r or r not in ALL_ROLES:
            continue
        defaults = static_permission_row(r)
        cleaned = {k: bool(row[k]) if k in row else defaults[k] for k in PERMISSION_KEYS}
        out[r] = cleaned
    _live_permissions = out


def role_permission(role: str | None, key: str) -> bool:
    """Эффективное право для роли (администратор всегда имеет все права)."""
    r = normalize_role(role)
    if r == ROLE_ADMIN:
        return True
    if key not in PERMISSION_KEYS:
        return False
    if _live_permissions is not None and r in _live_permissions:
        return bool(_live_permissions[r].get(key, False))
    return bool(static_permission_row(r).get(key, False))


def role_can_manage_employees(role: str | None) -> bool:
    return role_permission(role, PERMISSION_EMPLOYEE_MANAGE)


def role_can_view_dashboard(role: str | None) -> bool:
    return role_permission(role, PERMISSION_VIEW_DASHBOARD)


def role_can_mutate_franchises(role: str | None) -> bool:
    return role_permission(role, PERMISSION_FRANCHISE_WRITE)


def role_can_mutate_operational(role: str | None) -> bool:
    return role_permission(role, PERMISSION_OPERATIONAL_WRITE)


def role_can_mutate_content(role: str | None) -> bool:
    return role_permission(role, PERMISSION_CONTENT_WRITE)


def role_can_view_employees(role: str | None) -> bool:
    return role_permission(role, PERMISSION_EMPLOYEE_READ)


def merged_permissions_for_editing() -> dict[str, dict[str, bool]]:
    """Копия матрицы для диалога настроек (все роли кроме admin редактируемы отдельно)."""
    out: dict[str, dict[str, bool]] = {}
    for r in sorted(ALL_ROLES):
        if r == ROLE_ADMIN:
            continue
        row = static_permission_row(r)
        if _live_permissions and r in _live_permissions:
            row = deepcopy(_live_permissions[r])
        else:
            row = deepcopy(row)
        out[r] = row
    return out


ENTITY_EMPLOYEE = "Сотрудник"
ENTITY_FRANCHISE = "Франшиза"
CONTENT_ENTITIES: FrozenSet[str] = frozenset({"Сценарий", "Акт", "Часть"})
OPERATIONAL_ENTITIES: FrozenSet[str] = frozenset(
    {"Театр", "Зал", "Показ", "Клиент", "Билет", "Оборудование", "Услуга", "Аренда оборудования"}
)


def can_open_query(role: str | None, query_label: str) -> bool:
    if query_label == "Сотрудники":
        return role_can_view_employees(role)
    return True


def can_mutate_entity(role: str | None, entity_label: str | None) -> bool:
    """Право на добавление/редактирование/удаление записей данной сущности (согласовано с API)."""
    if not entity_label:
        return False
    r = normalize_role(role)
    if r == ROLE_ADMIN:
        return True
    if entity_label == ENTITY_EMPLOYEE:
        return role_permission(role, PERMISSION_EMPLOYEE_MANAGE)
    if entity_label == ENTITY_FRANCHISE:
        return role_permission(role, PERMISSION_FRANCHISE_WRITE)
    if entity_label in CONTENT_ENTITIES:
        return role_permission(role, PERMISSION_CONTENT_WRITE)
    if entity_label in OPERATIONAL_ENTITIES:
        return role_permission(role, PERMISSION_OPERATIONAL_WRITE)
    return False


def can_edit_entity(role: str | None, entity_label: str | None) -> bool:
    if entity_label == ENTITY_EMPLOYEE:
        return role_can_manage_employees(role)
    return can_mutate_entity(role, entity_label)


def can_delete_entity(role: str | None, entity_label: str | None) -> bool:
    return can_mutate_entity(role, entity_label)
