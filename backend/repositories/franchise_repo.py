"""
Репозиторий для работы с франчайзингами через API
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


def get_all_franchises() -> List[Dict]:
    """Получить все франчайзинги через API"""
    try:
        response = api_get(API_BASE_URL, "/franchises/")
        if response.status_code == 200:
            return response.json()
        logger.warning("Ошибка при получении франчайзингов: %s", response.status_code)
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /franchises/")
        return []


def add_franchise(
    contact_person,
    organization,
    phone,
    email,
    address,
    start_date,
    end_date,
    status,
    royalty_percentage,
    initial_fee,
    monthly_fee,
) -> bool:
    """Добавить франчайзинг через API"""
    try:
        franchise_data = {
            "contact_person": contact_person,
            "organization": organization,
            "phone": phone,
            "email": email,
            "address": address,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "royalty_percentage": royalty_percentage,
            "initial_fee": initial_fee,
            "monthly_fee": monthly_fee,
        }

        response = api_post(API_BASE_URL, "/franchises/", json=franchise_data)

        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /franchises/")
        return False


def update_franchise(
    contract_id,
    contact_person,
    organization,
    phone,
    email,
    address,
    start_date,
    end_date,
    status,
    royalty_percentage,
    initial_fee,
    monthly_fee,
) -> bool:
    """Обновить франчайзинг через API"""
    try:
        franchise_data = {
            "contact_person": contact_person,
            "organization": organization,
            "phone": phone,
            "email": email,
            "address": address,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "royalty_percentage": royalty_percentage,
            "initial_fee": initial_fee,
            "monthly_fee": monthly_fee,
        }
        response = api_put(API_BASE_URL, f"/franchises/{contract_id}", json=franchise_data)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /franchises/")
        return False
