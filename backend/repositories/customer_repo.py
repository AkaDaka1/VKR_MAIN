"""
Репозиторий для работы с клиентами через API
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


def get_all_customers() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/customers/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /customers/")
        return []


def add_customer(email: str, phone: str) -> bool:
    try:
        response = api_post(API_BASE_URL, "/customers/", json={"email": email, "phone": phone})
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /customers/")
        return False
