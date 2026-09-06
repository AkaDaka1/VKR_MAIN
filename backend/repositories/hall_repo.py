"""
Репозиторий для работы с залами через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from typing import List, Dict

from app.config import API_BASE_URL
from backend.http_client import api_get, api_post, api_put

logger = logging.getLogger(__name__)


def get_all_halls() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/halls/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /halls/")
        return []


def add_hall(theater_id: int, capacity: int) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/halls/",
            json={"theater_id": theater_id, "capacity": capacity},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /halls/")
        return False


def update_hall(hall_id: int, theater_id: int, capacity: int) -> bool:
    try:
        response = api_put(
            API_BASE_URL,
            f"/halls/{hall_id}",
            json={"theater_id": theater_id, "capacity": capacity},
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /halls/%s", hall_id)
        return False
