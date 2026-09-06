"""
Репозиторий для работы с театрами через API
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


def get_all_theaters() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/theaters/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /theaters/")
        return []


def add_theater(contract_id: int, name: str, location: str) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/theaters/",
            json={"contract_id": contract_id, "name": name, "location": location},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /theaters/")
        return False


def update_theater(theater_id: int, contract_id: int, name: str, location: str) -> bool:
    try:
        response = api_put(
            API_BASE_URL,
            f"/theaters/{theater_id}",
            json={"contract_id": contract_id, "name": name, "location": location},
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /theaters/%s", theater_id)
        return False
