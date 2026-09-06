"""
Репозиторий для работы со сценариями через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from typing import Any, Dict, List

from app.config import API_BASE_URL
from backend.http_client import api_get, api_post, api_post_multipart

logger = logging.getLogger(__name__)


def get_scenario(scenario_id: int) -> Dict[str, Any] | None:
    try:
        r = api_get(API_BASE_URL, f"/scenarios/{scenario_id}")
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /scenarios/%s", scenario_id)
        return None


def get_all_scenarios() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/scenarios/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /scenarios/")
        return []


def add_scenario(title: str, status: str, description: str) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/scenarios/",
            json={"title": title, "status": status, "description": description},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /scenarios/")
        return False


def upload_scenario_tz_file(scenario_id: int, local_file_path: str) -> tuple[bool, str]:
    """Загрузка файла ТЗ с диска клиента."""
    try:
        with open(local_file_path, "rb") as fh:
            files = {"file": (os.path.basename(local_file_path), fh)}
            r = api_post_multipart(
                API_BASE_URL,
                f"/scenarios/{scenario_id}/tz-spec/upload",
                files=files,
            )
        if r.status_code in (200, 201):
            return True, ""
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return False, str(detail)[:500]
    except OSError as e:
        return False, str(e)
    except requests.exceptions.RequestException:
        logger.exception("Ошибка загрузки ТЗ")
        return False, "Ошибка сети"


def download_scenario_tz_file(scenario_id: int, kind: str, dest_path: str) -> tuple[bool, str]:
    """kind: source | result — сохранить ответ API в dest_path."""
    if kind not in ("source", "result"):
        return False, "Неверный kind"
    try:
        r = api_get(API_BASE_URL, f"/scenarios/{scenario_id}/tz-spec/download?kind={kind}")
        if r.status_code != 200:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            return False, str(detail)[:500]
        with open(dest_path, "wb") as out:
            out.write(r.content)
        return True, ""
    except OSError as e:
        return False, str(e)
    except requests.exceptions.RequestException:
        logger.exception("Ошибка скачивания ТЗ")
        return False, "Ошибка сети"


def process_scenario_tz_n8n(scenario_id: int) -> tuple[bool, str, Dict[str, Any] | None]:
    """Вызов обработки на стороне API (n8n). При успехе возвращает обновлённый сценарий в payload."""
    try:
        r = api_post(API_BASE_URL, f"/scenarios/{scenario_id}/tz-spec/process", json={})
        if r.status_code in (200, 201):
            try:
                return True, "", r.json()
            except Exception:
                return True, "", None
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return False, str(detail)[:500], None
    except requests.exceptions.RequestException:
        logger.exception("Ошибка process ТЗ")
        return False, "Ошибка сети", None
