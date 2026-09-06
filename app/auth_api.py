"""
Модуль аутентификации через API
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from app.config import API_BASE_URL
from app.api_session import set_access_token

logger = logging.getLogger(__name__)


def authenticate(username: str, password: str):
    """
    Аутентификация пользователя через API.
    При успехе сохраняет JWT в api_session для последующих запросов репозиториев.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={
                "username": username,
                "password": password,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=(5, 30),
        )

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("Ответ /token без access_token")
                return None

            set_access_token(access_token)
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = requests.get(
                f"{API_BASE_URL}/users/me",
                headers=headers,
                timeout=(5, 30),
            )

            if user_response.status_code == 200:
                user_info = user_response.json()
                return {
                    "id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "role": user_info.get("role"),
                    "access_token": access_token,
                }
            else:
                logger.error("Ошибка при получении /users/me: %s", user_response.status_code)
                set_access_token(None)
                return None
        else:
            logger.error("Ошибка аутентификации: %s — %s", response.status_code, response.text[:500])
            set_access_token(None)
            return None
    except requests.exceptions.RequestException as e:
        logger.exception("Ошибка подключения к API")
        set_access_token(None)
        return None
