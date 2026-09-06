"""
Репозиторий для работы с сотрудниками через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from typing import List, Dict

from app.config import API_BASE_URL
from backend.http_client import api_delete, api_get, api_post, api_put

logger = logging.getLogger(__name__)


def get_all_employees() -> List[Dict]:
    """Получить всех сотрудников через API"""
    try:
        response = api_get(API_BASE_URL, "/employees/")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            logger.warning("Ответ GET /employees/ не список: %s", type(data).__name__)
            return []
        logger.warning("Ошибка при получении сотрудников: %s", response.status_code)
        return []
    except requests.exceptions.RequestException:
        logger.exception("Ошибка подключения к API")
        return []


def add_employee(username: str, password: str, role: str) -> bool:
    """Добавить сотрудника через API"""
    try:
        response = api_post(
            API_BASE_URL,
            "/employees/",
            json={"username": username, "password": password, "role": role},
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException:
        logger.exception("Ошибка POST /employees/")
        return False


def delete_employee_by_login(username: str) -> bool:
    """Удалить сотрудника по имени пользователя через API"""
    try:
        employees = get_all_employees()
        employee_id = None
        for emp in employees:
            if emp.get("username") == username:
                employee_id = emp.get("id")
                break

        if employee_id is not None:
            response = api_delete(API_BASE_URL, f"/employees/{employee_id}")
            return response.status_code == 200
        logger.warning("Сотрудник с именем %s не найден", username)
        return False
    except requests.exceptions.RequestException:
        logger.exception("Ошибка удаления сотрудника")
        return False


def update_last_online(username: str) -> bool:
    """Обновление last_online выполняется при аутентификации на сервере."""
    return True


def update_employee(employee_id: int, username: str, role: str, password: str | None = None) -> bool:
    """Обновить сотрудника через API"""
    try:
        payload = {"username": username, "role": role}
        if password:
            payload["password"] = password
        response = api_put(API_BASE_URL, f"/employees/{employee_id}", json=payload)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.exception("Ошибка PUT /employees/")
        return False
