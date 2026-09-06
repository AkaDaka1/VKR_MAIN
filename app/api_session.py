"""Хранение JWT после входа для запросов репозиториев к API."""
from __future__ import annotations

import threading
from typing import Optional

_lock = threading.Lock()
_token: Optional[str] = None


def set_access_token(token: str | None) -> None:
    global _token
    with _lock:
        _token = token.strip() if token else None


def get_access_token() -> Optional[str]:
    with _lock:
        return _token


def clear_access_token() -> None:
    set_access_token(None)


def auth_headers() -> dict[str, str]:
    t = get_access_token()
    if not t:
        return {}
    return {"Authorization": f"Bearer {t}"}
