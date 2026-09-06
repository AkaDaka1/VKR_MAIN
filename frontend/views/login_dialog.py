import logging
import sys
import os

# Добавляем корневую директорию проекта в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import QDialog, QMessageBox

logger = logging.getLogger(__name__)
from app.auth_api import authenticate
from frontend.ui.login_ui import Ui_Login
from frontend.views.ui_helpers import localize_dialog_buttons

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Login()
        self.ui.setupUi(self)
        localize_dialog_buttons(self.ui.buttonBoxPrimary)

        self.role = None
        self.username = None

        self.ui.buttonBoxPrimary.accepted.connect(self.try_login)
        self.ui.buttonBoxPrimary.rejected.connect(self.reject)

    def try_login(self):
        login = self.ui.loginInput.text()
        password = self.ui.passwordInput.text()

        user = authenticate(login, password)

        if user:
            logger.info("Успешный вход: %s", user.get("username"))
            self.role = user['role']
            self.username = user.get('username')
            self.accept()   # ← вручю закрываем
        else:
            QMessageBox.warning(
                self,
                "Ошибка входа",
                "Неверный логин или пароль"
            )
