"""
Репозиторий для работы с арендой оборудования через API
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


def get_all_rent_equipments() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/rents_equipment/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /rents_equipment/")
        return []


def add_rent_equipment(equipment_id: int, show_id: int, rent_start: str, rent_end: str) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/rents_equipment/",
            json={
                "equipment_id": equipment_id,
                "show_id": show_id,
                "rent_start": rent_start,
                "rent_end": rent_end,
            },
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /rents_equipment/")
        return False
