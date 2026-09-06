"""
Файл запуска основного приложения
"""
import faulthandler
import os
import sys

# При нативном падении Qt/Python иногда печатается трассировка в stderr (удобно для отладки).
faulthandler.enable(all_threads=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.auth_api import authenticate
from app.roles import set_role_permissions_matrix
from backend.repositories.permissions_repo import fetch_role_permissions
from frontend.views.login_dialog import LoginDialog
from frontend.views.main_window import MainWindow
from frontend.logging_setup import setup_client_logging


def load_style(app):
    root = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(root, "frontend", "ui", "style.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())


if __name__ == "__main__":
    setup_client_logging()
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass

    app = QApplication(sys.argv)
    load_style(app)
    app_font = QFont()
    app_font.setFamily("Segoe UI")
    app_font.setPointSize(13)
    app.setFont(app_font)

    login = LoginDialog()

    result = login.exec()

    if result:
        print("[SUCCESS] Логин успешен", flush=True)
        print("Роль пользователя:", login.role, flush=True)

        perms = fetch_role_permissions()
        set_role_permissions_matrix(perms)

        main_window = MainWindow(current_username=login.username, current_role=login.role)
        main_window.show()

        sys.exit(app.exec())
    else:
        print("[ERROR] Логин отменён или неуспешен", flush=True)

    sys.exit(0)
