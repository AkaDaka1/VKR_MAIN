"""Хранение файлов ТЗ для сценариев (исходник и результат n8n)."""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import config as api_config

ALLOWED_TZ_SUFFIXES = frozenset({".txt", ".md", ".pdf", ".doc", ".docx", ".rtf", ".odt"})
MAX_TZ_BYTES = 25 * 1024 * 1024


def upload_root() -> Path:
    p = Path(api_config.SCENARIO_TZ_UPLOAD_ROOT)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_resolve(relpath: str) -> Path:
    if not relpath or ".." in relpath.replace("\\", "/"):
        raise ValueError("invalid path")
    if relpath.startswith(("/", "\\")):
        raise ValueError("invalid path")
    base = upload_root().resolve()
    full = (base / relpath).resolve()
    full.relative_to(base)
    return full


def scenario_rel_prefix(scenario_id: int) -> str:
    return f"s{int(scenario_id)}"


def delete_stored_files(source_relpath: str | None, result_relpath: str | None) -> None:
    for rel in (source_relpath, result_relpath):
        if not rel:
            continue
        try:
            p = safe_resolve(rel)
            if p.is_file():
                p.unlink()
        except Exception:
            pass


def sanitize_original_filename(name: str) -> str:
    base = os.path.basename(name or "tz")
    base = re.sub(r"[^\w.\-()\s\u0400-\u04FF]", "_", base, flags=re.UNICODE).strip()
    return base[:240] if base else "tz"
