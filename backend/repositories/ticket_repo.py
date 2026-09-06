"""
Репозиторий для работы с билетами через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from typing import List, Dict, Any, Optional

from app.config import API_BASE_URL
from backend.http_client import api_get, api_post, api_put

logger = logging.getLogger(__name__)


def get_all_tickets() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/tickets/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /tickets/")
        return []


def add_ticket(owner_id: int, show_id: int, seat_number: str, price: float, status: str, vip_status: bool, email: str) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/tickets/",
            json={
                "owner_id": owner_id,
                "show_id": show_id,
                "seat_number": seat_number,
                "price": price,
                "status": status,
                "vip_status": vip_status,
                "email": email,
            },
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /tickets/")
        return False


def update_ticket(
    ticket_id: int,
    owner_id: Optional[int],
    show_id: int,
    seat_number: str,
    price: float,
    status: str,
    vip_status: bool,
    email: str,
) -> bool:
    try:
        payload: Dict[str, Any] = {
            "show_id": show_id,
            "seat_number": seat_number,
            "price": price,
            "status": status,
            "vip_status": vip_status,
            "email": email,
        }
        if owner_id is not None:
            payload["owner_id"] = owner_id
        else:
            payload["owner_id"] = None
        response = api_put(API_BASE_URL, f"/tickets/{ticket_id}", json=payload)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /tickets/%s", ticket_id)
        return False
