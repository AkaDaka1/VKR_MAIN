from PySide6.QtCore import QAbstractTableModel, Qt
from datetime import datetime


class GenericTableModel(QAbstractTableModel):
    """Generic model for showing list[dict] in QTableView."""

    def __init__(self, rows, columns, headers):
        super().__init__()
        self._rows = rows or []
        self._columns = columns or []
        self._headers = headers or columns or []

    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None

        r = index.row()
        if r < 0 or r >= len(self._rows):
            return None

        row = self._rows[r]
        key = self._columns[index.column()]
        value = row.get(key, "")
        return self._format_display_value(value)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    @staticmethod
    def _sort_key(value):
        if value is None:
            return (4, "")

        if isinstance(value, bool):
            return (0, int(value))

        if isinstance(value, (int, float)):
            return (0, value)

        text = str(value).strip()
        if text == "":
            return (4, "")

        # Numeric-like strings.
        try:
            return (0, float(text))
        except ValueError:
            pass

        # Datetime-like strings (common formats used in app/API).
        dt_formats = (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d.%m.%Y %H:%M:%S",
        )
        for fmt in dt_formats:
            try:
                return (1, datetime.strptime(text, fmt))
            except ValueError:
                continue

        return (2, text.lower())

    @staticmethod
    def _format_display_value(value):
        if value is None:
            return ""

        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y %H:%M:%S")

        text = str(value).strip()
        if not text:
            return ""

        dt_formats = (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d.%m.%Y %H:%M:%S",
        )
        for fmt in dt_formats:
            try:
                parsed = datetime.strptime(text, fmt)
                # For date-only values keep date only.
                if fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                    return parsed.strftime("%d.%m.%Y")
                return parsed.strftime("%d.%m.%Y %H:%M:%S")
            except ValueError:
                continue

        return text

    # Сортировка по клику на заголовок выполняется QSortFilterProxyModel (см. lessThan в main_window).
    # In-place sort() здесь давал конфликт с прокси и нативные падения на Windows при быстрых кликах.
