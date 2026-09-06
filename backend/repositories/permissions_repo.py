"""Загрузка и сохранение матрицы прав ролей через API."""
from __future__ import annotations

from typing import Any

from app.config import API_BASE_URL
from backend.http_client import api_get, api_put


def fetch_role_permissions() -> dict[str, dict[str, bool]] | None:
    r = api_get(API_BASE_URL, "/role-permissions")
    if r.status_code != 200:
        return None
    data = r.json()
    if not isinstance(data, dict):
        return None
    return data  # type: ignore[return-value]


def save_role_permissions(matrix: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, bool]] | None, str]:
    """Сохранить права. Возвращает (матрица с сервера при успехе, сообщение об ошибке)."""
    r = api_put(API_BASE_URL, "/role-permissions", json=matrix)
    if r.status_code != 200:
        detail = ""
        try:
            body = r.json()
            if isinstance(body, dict) and "detail" in body:
                d = body["detail"]
                detail = d if isinstance(d, str) else str(d)
        except Exception:
            detail = (r.text or "")[:500]
        return None, detail or f"HTTP {r.status_code}"
    try:
        out = r.json()
        if isinstance(out, dict):
            return out, ""  # type: ignore[return-value]
    except Exception:
        pass
    return None, "Пустой ответ сервера"
