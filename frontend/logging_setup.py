"""Настройка логирования десктоп-клиента: файл в LOCALAPPDATA и консоль."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


class _FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        try:
            self.flush()
        except OSError:
            pass


def install_uncaught_exception_hook() -> None:
    """Писать в лог любые необработанные исключения Python (не ловит нативные краши Qt)."""

    def _hook(exc_type, exc, tb):
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc, tb)
            return
        logging.getLogger("vkrt.uncaught").critical(
            "Необработанное исключение",
            exc_info=(exc_type, exc, tb),
        )
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


def setup_client_logging(level: int = logging.INFO) -> Path | None:
    """
    Пишет логи в %LOCALAPPDATA%\\VKR_MAIN\\logs\\client.log (Windows)
    и дублирует INFO+ в stderr.
    """
    try:
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        else:
            base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
        log_dir = Path(base) / "VKR_MAIN" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "client.log"

        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

        root = logging.getLogger()
        root.setLevel(level)

        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(fmt)

        sh = _FlushingStreamHandler(sys.stderr)
        sh.setLevel(level)
        sh.setFormatter(fmt)

        root.handlers.clear()
        root.addHandler(fh)
        root.addHandler(sh)

        logging.getLogger(__name__).info("Логирование клиента: %s", log_path)
        install_uncaught_exception_hook()
        return log_path
    except OSError as e:
        logging.basicConfig(level=level)
        logging.getLogger(__name__).warning("Не удалось настроить файл логов: %s", e)
        install_uncaught_exception_hook()
        return None
