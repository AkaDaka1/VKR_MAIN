"""
Репозиторий для работы с частями через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from typing import List, Dict

from app.config import API_BASE_URL
from backend.http_client import api_get, api_post

logger = logging.getLogger(__name__)


def get_all_parts() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/parts/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /parts/")
        return []


def add_part(act_id: int, title: str, file_path: str, position: int) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/parts/",
            json={"act_id": act_id, "title": title, "file_path": file_path, "position": position},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /parts/")
        return False
