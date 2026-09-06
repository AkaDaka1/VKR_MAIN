"""Общие HTTP-вызовы для репозиториев: таймауты и логирование."""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

# (connect timeout, read timeout) в секундах
DEFAULT_TIMEOUT = (5, 60)


def _join(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _merge_headers(extra: dict[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        from app.api_session import auth_headers

        out.update(auth_headers())
    except Exception:
        pass
    if extra:
        out.update(extra)
    return out


def _log_bad_status(method: str, url: str, response: requests.Response) -> None:
    if response.status_code >= 400:
        body = ""
        try:
            body = response.text[:500]
        except Exception:
            pass
        logger.warning("HTTP %s %s -> %s %s", method, url, response.status_code, body)


def api_put(
    base_url: str,
    path: str,
    json: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    url = _join(base_url, path)
    logger.debug("PUT %s", url)
    try:
        r = requests.put(url, json=json, headers=_merge_headers(headers), timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.exception("Сбой сети PUT %s", url)
        raise
    _log_bad_status("PUT", url, r)
    return r


def api_get(base_url: str, path: str, headers: dict[str, str] | None = None) -> requests.Response:
    url = _join(base_url, path)
    logger.debug("GET %s", url)
    try:
        r = requests.get(url, headers=_merge_headers(headers), timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.exception("Сбой сети GET %s", url)
        raise
    _log_bad_status("GET", url, r)
    return r


def api_post_multipart(
    base_url: str,
    path: str,
    files: dict,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    url = _join(base_url, path)
    h = _merge_headers(headers)
    h.pop("Content-Type", None)
    logger.debug("POST multipart %s", url)
    try:
        r = requests.post(url, files=files, data=data, headers=h, timeout=(5, 300))
    except requests.exceptions.RequestException:
        logger.exception("Сбой сети POST multipart %s", url)
        raise
    _log_bad_status("POST", url, r)
    return r


def api_post(
    base_url: str,
    path: str,
    json: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    url = _join(base_url, path)
    logger.debug("POST %s", url)
    try:
        r = requests.post(url, json=json, headers=_merge_headers(headers), timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.exception("Сбой сети POST %s", url)
        raise
    _log_bad_status("POST", url, r)
    return r


def api_delete(base_url: str, path: str, headers: dict[str, str] | None = None) -> requests.Response:
    url = _join(base_url, path)
    logger.debug("DELETE %s", url)
    try:
        r = requests.delete(url, headers=_merge_headers(headers), timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.exception("Сбой сети DELETE %s", url)
        raise
    _log_bad_status("DELETE", url, r)
    return r
