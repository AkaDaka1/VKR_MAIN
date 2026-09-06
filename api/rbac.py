"""Проверка ролей для защищённых маршрутов FastAPI."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.roles import ALL_ROLES, ROLE_ADMIN, normalize_role

from . import crud, models
from .auth import get_current_user
from .database import get_db


async def require_any_authenticated_user(
    user: models.Employee = Depends(get_current_user),
) -> models.Employee:
    r = normalize_role(user.role)
    if r not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неизвестная роль учётной записи. Обратитесь к администратору.",
        )
    return user


def require_roles(*allowed_roles: str):
    """
    Допускает указанные роли и всегда администратора.
    Использовать после require_any_authenticated_user по цепочке Depends нельзя —
    поэтому внутри снова вызываем get_current_user через общую проверку.
    """
    allowed = frozenset(allowed_roles) | {"admin"}

    async def checker(user: models.Employee = Depends(require_any_authenticated_user)) -> models.Employee:
        r = normalize_role(user.role)
        if r not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для этой операции.",
            )
        return user

    return checker


def require_permission(permission_key: str):
    """Доступ по ключу права из матрицы (администратор всегда допускается)."""

    def checker(
        user: models.Employee = Depends(require_any_authenticated_user),
        db: Session = Depends(get_db),
    ) -> models.Employee:
        r = normalize_role(user.role)
        if r == ROLE_ADMIN:
            return user
        if crud.user_has_permission(db, r, permission_key):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для этой операции.",
        )

    return checker
