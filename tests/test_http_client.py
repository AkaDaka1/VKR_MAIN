"""Юнит-тесты без БД и без поднятого API."""
from backend.http_client import _join


def test_join_base_and_path():
    assert _join("http://localhost:8000", "/theaters/") == "http://localhost:8000/theaters/"
    assert _join("http://localhost:8000/", "halls") == "http://localhost:8000/halls"
