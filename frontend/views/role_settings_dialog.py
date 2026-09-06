"""Диалог настройки прав ролей (только для администратора)."""
from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.roles import (
    ALL_ROLES,
    PERMISSION_KEYS,
    PERMISSION_LABELS_RU,
    ROLE_ADMIN,
    ROLE_LABELS_RU,
    merged_permissions_for_editing,
)
from backend.repositories.permissions_repo import fetch_role_permissions, save_role_permissions


class RoleSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки прав ролей")
        self.resize(900, 560)
        self.saved_matrix: dict[str, dict[str, bool]] | None = None

        self._matrix = self._load_initial_matrix()
        self._checkboxes: dict[tuple[str, str], QCheckBox] = {}

        root = QVBoxLayout(self)
        intro = QLabel(
            "Отметьте, какие действия разрешены для каждой роли. "
            "Администратор всегда имеет полный доступ; его строка в таблице не редактируется."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setColumnStretch(0, 1)

        editable_roles = [r for r in sorted(ALL_ROLES) if r != ROLE_ADMIN]

        header = QLabel("Право")
        header.setStyleSheet("font-weight: 600;")
        grid.addWidget(header, 0, 0)
        for col, role in enumerate(editable_roles, start=1):
            lab = QLabel(ROLE_LABELS_RU.get(role, role))
            lab.setStyleSheet("font-weight: 600;")
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lab, 0, col)

        for row, key in enumerate(PERMISSION_KEYS, start=1):
            plab = QLabel(PERMISSION_LABELS_RU.get(key, key))
            plab.setWordWrap(True)
            plab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            grid.addWidget(plab, row, 0)
            for col, role in enumerate(editable_roles, start=1):
                cb = QCheckBox()
                cb.setChecked(bool(self._matrix.get(role, {}).get(key, False)))
                cb.setTristate(False)
                self._checkboxes[(role, key)] = cb
                grid.addWidget(cb, row, col, Qt.AlignmentFlag.AlignCenter)

        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _load_initial_matrix(self) -> dict[str, dict[str, bool]]:
        base = merged_permissions_for_editing()
        remote = fetch_role_permissions()
        if not remote:
            return base
        for role, row in remote.items():
            r = (role or "").strip()
            if r == ROLE_ADMIN or r not in base:
                continue
            if isinstance(row, dict):
                for k in PERMISSION_KEYS:
                    if k in row:
                        base[r][k] = bool(row[k])
        return base

    def _collect(self) -> dict[str, dict[str, bool]]:
        out: dict[str, dict[str, bool]] = {}
        for role in (r for r in sorted(ALL_ROLES) if r != ROLE_ADMIN):
            row: dict[str, bool] = {}
            for key in PERMISSION_KEYS:
                cb = self._checkboxes.get((role, key))
                row[key] = cb.isChecked() if cb else False
            out[role] = row
        return out

    def _on_save(self):
        payload = self._collect()
        saved, err = save_role_permissions(payload)
        if saved is None:
            QMessageBox.warning(self, "Не удалось сохранить", err or "Неизвестная ошибка")
            return
        self.saved_matrix = deepcopy(saved)
        self.accept()
