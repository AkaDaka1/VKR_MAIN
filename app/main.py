"""
Устаревшая точка входа (исторические пути views/, qt/).

Используйте из корня проекта:
    python start_app.py
"""
from __future__ import annotations

import sys


def main() -> None:
    print(
        "Этот файл больше не используется. Запустите клиент из корня проекта:\n"
        "  python start_app.py",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
