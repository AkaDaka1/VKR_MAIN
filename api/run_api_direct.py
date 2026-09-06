"""
Точка входа для uvicorn: реэкспорт `app` (см. start_api.py).

Запуск из корня проекта:
    uvicorn api.api:app --reload
или:
    python start_api.py
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from api.api import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.api:app", host="127.0.0.1", port=8000, reload=True)
