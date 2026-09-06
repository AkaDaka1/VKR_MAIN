"""
Репозиторий для работы с шоу через API
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


def get_all_shows() -> List[Dict]:
    try:
        response = api_get(API_BASE_URL, "/shows/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка GET /shows/")
        return []


def add_show(hall_id: int, scenario_id: int, title: str, vote_type: str, duration: str, show_date: str) -> bool:
    try:
        response = api_post(
            API_BASE_URL,
            "/shows/",
            json={
                "hall_id": hall_id,
                "scenario_id": scenario_id,
                "title": title,
                "vote_type": vote_type,
                "duration": duration,
                "show_date": show_date,
            },
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /shows/")
        return False


def update_show(
    show_id: int,
    hall_id: int,
    scenario_id: Optional[int],
    title: str,
    vote_type: str,
    duration: str,
    show_date: str,
) -> bool:
    try:
        payload: Dict[str, Any] = {
            "hall_id": hall_id,
            "title": title,
            "vote_type": vote_type,
            "duration": duration,
            "show_date": show_date,
            "scenario_id": scenario_id,
        }
        response = api_put(API_BASE_URL, f"/shows/{show_id}", json=payload)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /shows/%s", show_id)
        return False
