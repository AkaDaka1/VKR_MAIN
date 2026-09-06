"""
Репозиторий для работы с оборудованием через API
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


def get_all_equipments() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/equipments/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /equipments/")
        return []


def add_equipment(name: str, price: float, amount: int) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/equipments/",
            json={"name": name, "price": price, "amount": amount},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /equipments/")
        return False
