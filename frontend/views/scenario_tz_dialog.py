"""Диалог: файл ТЗ сценария (загрузка, вызов n8n, скачивание)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from app.roles import can_mutate_entity
from backend.repositories.scenario_repo import (
    get_scenario,
    upload_scenario_tz_file,
    download_scenario_tz_file,
    process_scenario_tz_n8n,
)

_STATUS_RU = {
    None: "—",
    "": "—",
    "none": "нет файла",
    "uploaded": "исходник загружен",
    "pending": "обработка…",
    "ready": "результат готов",
    "error": "ошибка обработки",
}


class ScenarioTzDialog(QDialog):
    def __init__(self, parent, scenario_id: int, current_role: str | None, scenario_title: str = "", on_changed=None):
        super().__init__(parent)
        self.scenario_id = scenario_id
        self.current_role = current_role
        self._on_changed = on_changed
        self.setWindowTitle(f"ТЗ сценария — {scenario_title or f'ID {scenario_id}'}")
        self.setMinimumWidth(420)

        self._info_title = QLabel(self)
        self._info_source = QLabel(self)
        self._info_result = QLabel(self)
        self._info_status = QLabel(self)

        self._btn_upload = QPushButton("Загрузить файл ТЗ…", self)
        self._btn_upload.clicked.connect(self._do_upload)
        self._btn_process = QPushButton("Отправить в обработку (n8n)…", self)
        self._btn_process.clicked.connect(self._do_process)
        self._btn_dl_source = QPushButton("Скачать исходник", self)
        self._btn_dl_source.clicked.connect(lambda: self._do_download("source"))
        self._btn_dl_result = QPushButton("Скачать результат", self)
        self._btn_dl_result.clicked.connect(lambda: self._do_download("result"))
        self._btn_close = QPushButton("Закрыть", self)
        self._btn_close.clicked.connect(self.accept)

        row_btns = QHBoxLayout()
        row_btns.addWidget(self._btn_upload)
        row_btns.addWidget(self._btn_process)

        row_dl = QHBoxLayout()
        row_dl.addWidget(self._btn_dl_source)
        row_dl.addWidget(self._btn_dl_result)

        layout = QVBoxLayout(self)
        layout.addWidget(self._info_title)
        layout.addWidget(self._info_source)
        layout.addWidget(self._info_result)
        layout.addWidget(self._info_status)
        layout.addLayout(row_btns)
        layout.addLayout(row_dl)
        layout.addWidget(self._btn_close)

        self._apply_write_permissions()
        self._refresh_labels()

    def _apply_write_permissions(self):
        w = can_mutate_entity(self.current_role, "Сценарий")
        self._btn_upload.setEnabled(w)
        self._btn_process.setEnabled(w)
        if not w:
            self._btn_upload.setToolTip("Нужны права на изменение контента (сценарист / администратор).")
            self._btn_process.setToolTip("Нужны права на изменение контента (сценарист / администратор).")

    def _notify_changed(self):
        if callable(self._on_changed):
            self._on_changed()

    def _refresh_labels(self):
        data = get_scenario(self.scenario_id)
        if not data:
            self._info_title.setText("Не удалось загрузить данные сценария.")
            self._info_source.setText("")
            self._info_result.setText("")
            self._info_status.setText("")
            self._btn_dl_source.setEnabled(False)
            self._btn_dl_result.setEnabled(False)
            self._btn_process.setEnabled(False)
            return

        title = data.get("title") or ""
        self._info_title.setText(f"<b>Сценарий #{self.scenario_id}</b> {title}")
        src = data.get("tz_source_filename") or "—"
        res = data.get("tz_result_filename") or "—"
        st = data.get("tz_pipeline_status")
        self._info_source.setText(f"Исходный файл: {src}")
        self._info_result.setText(f"Результат обработки: {res}")
        self._info_status.setText(f"Статус: {_STATUS_RU.get(st, st or '—')}")

        self._btn_dl_source.setEnabled(bool(data.get("tz_source_filename")))
        self._btn_dl_result.setEnabled(bool(data.get("tz_result_filename")))
        self._apply_write_permissions()

    def _do_upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл ТЗ",
            "",
            "Документы (*.txt *.md *.pdf *.doc *.docx *.rtf *.odt);;Все файлы (*.*)",
        )
        if not path:
            return
        ok, err = upload_scenario_tz_file(self.scenario_id, path)
        if ok:
            QMessageBox.information(self, "ТЗ", "Файл загружен.")
            self._refresh_labels()
            self._notify_changed()
        else:
            QMessageBox.warning(self, "Ошибка", err or "Не удалось загрузить файл.")

    def _do_process(self):
        ok, err, _payload = process_scenario_tz_n8n(self.scenario_id)
        if ok:
            QMessageBox.information(self, "ТЗ", "Обработка завершена, результат сохранён.")
            self._refresh_labels()
            self._notify_changed()
        else:
            QMessageBox.warning(self, "Ошибка", err or "Не удалось выполнить обработку.")

    def _do_download(self, kind: str):
        data = get_scenario(self.scenario_id)
        if not data:
            QMessageBox.warning(self, "Ошибка", "Нет данных сценария.")
            return
        default = (data.get("tz_source_filename") if kind == "source" else data.get("tz_result_filename")) or "tz.bin"
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", default, "Все файлы (*.*)")
        if not path:
            return
        ok, err = download_scenario_tz_file(self.scenario_id, kind, path)
        if ok:
            QMessageBox.information(self, "ТЗ", "Файл сохранён.")
        else:
            QMessageBox.warning(self, "Ошибка", err or "Не удалось скачать файл.")
