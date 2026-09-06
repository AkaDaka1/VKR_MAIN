from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QMessageBox,
    QComboBox,
    QPushButton,
    QDateEdit,
    QDateTimeEdit,
)
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Qt
from PySide6.QtCore import QDate, QDateTime
from frontend.qt_font_utils import safe_derived_font
from frontend.views.ui_helpers import localize_dialog_buttons


class GenericAddDialog(QDialog):
    """Reusable dialog for creating entities with text fields and combos."""

    def __init__(
        self,
        title: str,
        fields,
        test_data: dict | None = None,
        initial_data: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._fields = self._normalize_fields(fields)
        self._inputs = {}
        self._test_data = test_data or {}
        self._initial_data = initial_data or {}
        self._build_ui()
        self._apply_initial_data()

    @staticmethod
    def _normalize_fields(fields):
        normalized = []
        for field in fields:
            if isinstance(field, tuple):
                key, label = field
                normalized.append({"key": key, "label": label, "widget": "line"})
            else:
                normalized.append(field)
        return normalized

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for field in self._fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")

            if widget_type == "combo":
                input_widget = QComboBox(self)
                # Не копировать QFont(self.font()) вслепую: после QSS с font-size в px pointSize() == -1,
                # из-за этого Qt пишет предупреждения и возможны нестабильности при открытии popup.
                # view().setFont() не вызываем — см. комментарий про краш на Windows при закрытии диалога.
                input_widget.setFont(safe_derived_font(self.font(), default_point=10))
                options = field.get("options", [])
                for option_label, option_value in options:
                    input_widget.addItem(option_label, option_value)
            elif widget_type == "date":
                input_widget = QDateEdit(self)
                input_widget.setCalendarPopup(True)
                input_widget.setDisplayFormat("dd.MM.yyyy")
                input_widget.setDate(QDate.currentDate())
            elif widget_type == "datetime":
                input_widget = QDateTimeEdit(self)
                input_widget.setCalendarPopup(True)
                input_widget.setDisplayFormat("dd.MM.yyyy HH:mm:ss")
                input_widget.setDateTime(QDateTime.currentDateTime())
            else:
                input_widget = QLineEdit(self)
                input_mask = field.get("input_mask")
                if input_mask:
                    input_widget.setInputMask(input_mask)

            form_layout.addRow(f"{label}:", input_widget)
            self._inputs[key] = input_widget

        root_layout.addLayout(form_layout)

        if self._test_data:
            self.fill_test_btn = QPushButton("🧪 Заполнить тестовыми данными", self)
            self.fill_test_btn.clicked.connect(self.fill_test_data)
            self.fill_test_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                """
            )
            root_layout.addWidget(self.fill_test_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setObjectName("buttonBoxPrimary")
        localize_dialog_buttons(buttons)
        buttons.accepted.connect(self._on_accept_requested)
        buttons.rejected.connect(self._on_reject_requested)
        root_layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Keep Ok/Cancel visually identical and centered.
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_btn and cancel_btn:
            target_width = max(ok_btn.sizeHint().width(), cancel_btn.sizeHint().width(), 120)
            ok_btn.setMinimumWidth(target_width)
            cancel_btn.setMinimumWidth(target_width)

    def _close_combo_popups(self) -> None:
        """Скрыть выпадающие списки QComboBox до уничтожения диалога.

        На Windows в Qt 6 / PySide6 закрытие модального окна с открытым или
        недавно использованным popup комбобокса может приводить к падению процесса.
        """
        for w in self._inputs.values():
            if isinstance(w, QComboBox):
                w.hidePopup()

    def _on_accept_requested(self) -> None:
        self._close_combo_popups()
        self.accept()

    def _on_reject_requested(self) -> None:
        self._close_combo_popups()
        self.reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        self._close_combo_popups()
        super().closeEvent(event)

    def get_raw_values(self) -> dict:
        values = {}
        for field in self._fields:
            key = field["key"]
            widget_type = field.get("widget", "line")
            widget = self._inputs[key]

            if widget_type == "combo":
                values[key] = widget.currentData()
            elif widget_type == "date":
                values[key] = widget.date().toString("yyyy-MM-dd")
            elif widget_type == "datetime":
                values[key] = widget.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
            else:
                values[key] = widget.text().strip()
        return values

    def fill_test_data(self):
        for field in self._fields:
            key = field["key"]
            if key not in self._test_data:
                continue

            widget = self._inputs[key]
            test_value = self._test_data[key]
            widget_type = field.get("widget", "line")

            if widget_type == "combo":
                index_by_data = widget.findData(test_value)
                if index_by_data >= 0:
                    widget.setCurrentIndex(index_by_data)
                    continue

                index_by_text = widget.findText(str(test_value))
                if index_by_text >= 0:
                    widget.setCurrentIndex(index_by_text)
            elif widget_type == "date":
                date_value = QDate.fromString(str(test_value), "yyyy-MM-dd")
                if date_value.isValid():
                    widget.setDate(date_value)
            elif widget_type == "datetime":
                dt_value = QDateTime.fromString(str(test_value), "yyyy-MM-ddTHH:mm:ss")
                if dt_value.isValid():
                    widget.setDateTime(dt_value)
            else:
                widget.setText(str(test_value))

    def _apply_initial_data(self):
        for field in self._fields:
            key = field["key"]
            if key not in self._initial_data:
                continue

            widget = self._inputs[key]
            value = self._initial_data[key]
            widget_type = field.get("widget", "line")

            if widget_type == "combo":
                index_by_data = widget.findData(value)
                if index_by_data >= 0:
                    widget.setCurrentIndex(index_by_data)
                    continue
                index_by_text = widget.findText(str(value))
                if index_by_text >= 0:
                    widget.setCurrentIndex(index_by_text)
            elif widget_type == "date":
                date_value = QDate.fromString(str(value), "yyyy-MM-dd")
                if date_value.isValid():
                    widget.setDate(date_value)
            elif widget_type == "datetime":
                dt_value = QDateTime.fromString(str(value), "yyyy-MM-ddTHH:mm:ss")
                if dt_value.isValid():
                    widget.setDateTime(dt_value)
            else:
                widget.setText("" if value is None else str(value))

    @staticmethod
    def parse_value(raw_value: str, value_type: str):
        if value_type == "str":
            return raw_value
        if value_type == "int":
            return int(raw_value)
        if value_type == "float":
            return float(raw_value)
        if value_type == "bool":
            lowered = raw_value.lower()
            if lowered in {"1", "true", "yes", "y", "да"}:
                return True
            if lowered in {"0", "false", "no", "n", "нет"}:
                return False
            raise ValueError("bool")
        raise ValueError(value_type)

    @staticmethod
    def show_parse_error(parent, field_label: str, expected_type: str):
        QMessageBox.warning(
            parent,
            "Ошибка ввода",
            f"Поле '{field_label}' должно быть типа {expected_type}.",
        )
