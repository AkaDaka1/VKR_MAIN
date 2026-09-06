from PySide6.QtCore import Qt, QThread, Signal, QSortFilterProxyModel, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QHeaderView,
    QDialog,
    QMessageBox,
    QDialogButtonBox,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
)
import logging
import time
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

from frontend.ui.main_ui import Ui_MainWindow
from frontend.views.generic_add_dialog import GenericAddDialog
from frontend.views.scenario_tz_dialog import ScenarioTzDialog
from frontend.views.models.generic_table_model import GenericTableModel
from backend.repositories.theater_repo import add_theater, get_all_theaters, update_theater
from backend.repositories.hall_repo import add_hall, get_all_halls, update_hall
from backend.repositories.scenario_repo import add_scenario
from backend.repositories.scenario_repo import get_all_scenarios
from backend.repositories.act_repo import add_act
from backend.repositories.act_repo import get_all_acts
from backend.repositories.part_repo import add_part, get_all_parts
from backend.repositories.show_repo import add_show, get_all_shows, update_show
from backend.repositories.customer_repo import get_all_customers
from backend.repositories.customer_repo import add_customer
from backend.repositories.ticket_repo import add_ticket, get_all_tickets, update_ticket
from backend.repositories.equipment_repo import get_all_equipments
from backend.repositories.equipment_repo import add_equipment
from backend.repositories.service_repo import add_service, get_all_services
from backend.repositories.rent_equipment_repo import add_rent_equipment, get_all_rent_equipments
from backend.repositories.franchise_repo import get_all_franchises, add_franchise, update_franchise
from backend.repositories.employee_repo import add_employee, get_all_employees, update_employee
from app.config import API_BASE_URL
from app.roles import (
    ROLE_ADMIN,
    ROLE_COMBO_OPTIONS,
    can_delete_entity,
    can_edit_entity,
    can_mutate_entity,
    can_open_query,
    normalize_role,
    role_can_view_dashboard,
    set_role_permissions_matrix,
)
from backend.http_client import api_delete

# Максимальная длина строковых полей при добавлении сущности (защита от случайного мусора)
_MAX_STRING_FIELD_LEN = 500


class QueryFetchThread(QThread):
    """Фоновая загрузка выборки без QObject в чужом потоке (безопасно с deleteLater)."""

    load_ok = Signal(int, object)
    load_err = Signal(int, str)

    def __init__(self, request_id: int, fetch_fn, parent=None):
        super().__init__(parent)
        self._request_id = request_id
        self._fetch_fn = fetch_fn

    def run(self):
        try:
            rows = self._fetch_fn()
            if not isinstance(rows, list):
                rows = []
            self.load_ok.emit(self._request_id, rows)
        except Exception as e:
            self.load_err.emit(self._request_id, str(e))


class GlobalFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._needle = ""

    def lessThan(self, source_left, source_right):
        if not source_left.isValid() or not source_right.isValid():
            return False
        sm = self.sourceModel()
        if sm is None:
            return False
        try:
            l = sm.data(source_left, Qt.ItemDataRole.DisplayRole)
            r = sm.data(source_right, Qt.ItemDataRole.DisplayRole)
            lk = GenericTableModel._sort_key(l)
            rk = GenericTableModel._sort_key(r)
            return lk < rk
        except Exception:
            logger.exception("Ошибка сравнения строк при сортировке таблицы")
            return False

    def set_filter_text(self, text: str):
        self._needle = (text or "").strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._needle:
            return True
        model = self.sourceModel()
        if model is None:
            return True
        columns = model.columnCount()
        for col in range(columns):
            idx = model.index(source_row, col, source_parent)
            text = str(model.data(idx, Qt.DisplayRole) or "")
            if self._needle in text.lower():
                return True
        return False


class DashboardFetchThread(QThread):
    """Дашборд в фоне без worker-QObject в дополнительном потоке."""

    load_ok = Signal(dict)
    load_err = Signal(str)

    def run(self):
        try:
            stats = {
                "employees": len(get_all_employees() or []),
                "franchises": len(get_all_franchises() or []),
                "shows": len(get_all_shows() or []),
                "customers": len(get_all_customers() or []),
            }
            self.load_ok.emit(stats)
        except Exception as e:
            self.load_err.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self, current_username=None, current_role=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.localize_menu_texts()
        self.current_username = current_username
        self.current_role = current_role

        self.ui.Employees.triggered.connect(self.show_employees)
        self.ui.actionFranchise.triggered.connect(self.show_franchises)
        self.ui.actionRefresh.triggered.connect(self.refresh_current_query)

        # Create and connect the "Add Employee" and "Remove Employee" actions
        self.add_employee_action = None
        self.add_franchise_action = None
        self.dynamic_add_actions = []
        self.dynamic_query_actions = []
        self.dynamic_remove_actions = []
        self._query_specs_by_label = {}
        self._add_specs_by_label = {}
        self._remove_specs_by_label = {}
        self._query_cache = {}
        self._query_cache_ttl_sec = 20
        self._active_query_request_id = 0
        self._active_query_label = None
        self._query_threads = {}
        self._query_request_specs = {}
        self._proxy_model = None
        self._dashboard_thread = None
        self._dashboard_running = False
        self._dashboard_silent_request = False
        self._dashboard_refresh_pending = False
        self._active_query_entity_label = None
        self._query_to_entity = {}
        self._entity_to_query = {}
        self._setup_top_panels()
        self.create_menu_actions()
        self._setup_role_settings_action()
        self._apply_role_restrictions()
        self._sync_quick_action_buttons()
        self.dashboard_timer = QTimer(self)
        self.dashboard_timer.setInterval(30000)
        self.dashboard_timer.timeout.connect(self.refresh_dashboard_silent)
        if role_can_view_dashboard(self.current_role):
            self.dashboard_timer.start()
            self.refresh_dashboard(force=True)

    def localize_menu_texts(self):
        """Translate base menu/actions from main.ui to Russian."""
        self.setWindowTitle("Система управления театром")
        self.ui.menu.setTitle("База данных")
        self.ui.menuAdd.setTitle("Добавить")
        self.ui.menuQuery.setTitle("Выборка")
        self.ui.menuRemove.setTitle("Удалить")

        self.ui.actionRefresh.setText("Обновить")
        self.ui.Employees.setText("Сотрудники")
        self.ui.actionFranchise.setText("Франшизы")
        self.ui.actionEmployee.setText("Сотрудник")
        self.ui.actionEmployee_2.setText("Сотрудник")
        self.ui.actionFranchise_2.setText("Франшиза")

    def _setup_top_panels(self):
        top_container = QWidget(self)
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        self.actions_row = QWidget(top_container)
        actions_layout = QHBoxLayout(self.actions_row)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        self.quick_add_btn = QPushButton("Добавить", self.actions_row)
        self.quick_edit_btn = QPushButton("Редактировать", self.actions_row)
        self.quick_delete_btn = QPushButton("Удалить", self.actions_row)
        self.quick_refresh_btn = QPushButton("Обновить выборку", self.actions_row)
        self.quick_scenario_tz_btn = QPushButton("ТЗ сценария", self.actions_row)
        self.quick_add_btn.setObjectName("topPanelAction")
        self.quick_edit_btn.setObjectName("topPanelAction")
        self.quick_delete_btn.setObjectName("topPanelAction")
        self.quick_refresh_btn.setObjectName("topPanelAction")
        self.quick_scenario_tz_btn.setObjectName("topPanelAction")
        self.search_input = QLineEdit(self.actions_row)
        self.search_input.setPlaceholderText("Глобальный поиск по текущей таблице...")
        self.search_input.textChanged.connect(self._on_global_search_changed)
        self.quick_add_btn.clicked.connect(self.quick_add_current_entity)
        self.quick_edit_btn.clicked.connect(self.quick_edit_current_entity)
        self.quick_delete_btn.clicked.connect(self.quick_remove_current_entity)
        self.quick_refresh_btn.clicked.connect(self.refresh_current_query)
        self.quick_scenario_tz_btn.clicked.connect(self._open_scenario_tz_dialog)
        actions_layout.addWidget(self.quick_add_btn)
        actions_layout.addWidget(self.quick_edit_btn)
        actions_layout.addWidget(self.quick_delete_btn)
        actions_layout.addWidget(self.quick_refresh_btn)
        actions_layout.addWidget(self.quick_scenario_tz_btn)
        actions_layout.addWidget(self.search_input, 1)

        top_layout.addWidget(self.actions_row)

        self.dashboard_panel = QFrame(top_container)
        self.dashboard_panel.setObjectName("dashboardPanel")
        dashboard_layout = QHBoxLayout(self.dashboard_panel)
        dashboard_layout.setContentsMargins(12, 10, 12, 10)
        dashboard_layout.setSpacing(14)
        self.dashboard_title = QLabel("Дашборд", self.dashboard_panel)
        self.dashboard_title.setObjectName("dashboardTitle")
        dashboard_layout.addWidget(self.dashboard_title)
        self.dashboard_labels = {
            "employees": QLabel("Сотрудники: ...", self.dashboard_panel),
            "franchises": QLabel("Франшизы: ...", self.dashboard_panel),
            "shows": QLabel("Показы: ...", self.dashboard_panel),
            "customers": QLabel("Клиенты: ...", self.dashboard_panel),
        }
        for label in self.dashboard_labels.values():
            label.setObjectName("dashboardStat")
            dashboard_layout.addWidget(label)
        self.refresh_dashboard_btn = QPushButton("Обновить дашборд", self.dashboard_panel)
        self.refresh_dashboard_btn.setObjectName("topPanelAction")
        self.refresh_dashboard_btn.clicked.connect(self.refresh_dashboard)
        dashboard_layout.addStretch()
        dashboard_layout.addWidget(self.refresh_dashboard_btn)

        top_layout.addWidget(self.dashboard_panel)
        self.ui.verticalLayout.insertWidget(0, top_container)
        self.dashboard_panel.setVisible(role_can_view_dashboard(self.current_role))

    def _setup_role_settings_action(self):
        self._action_role_settings = QAction("Настройки прав…", self)
        self._action_role_settings.triggered.connect(self._open_role_settings)
        self.ui.menubar.addAction(self._action_role_settings)
        self._action_role_settings.setVisible(normalize_role(self.current_role) == ROLE_ADMIN)

    def _open_role_settings(self):
        from frontend.views.role_settings_dialog import RoleSettingsDialog

        dlg = RoleSettingsDialog(self)
        if dlg.exec() != QDialog.Accepted or dlg.saved_matrix is None:
            return
        set_role_permissions_matrix(dlg.saved_matrix)
        self._apply_role_restrictions()
        self._sync_quick_action_buttons()
        vis = role_can_view_dashboard(self.current_role)
        self.dashboard_panel.setVisible(vis)
        if vis:
            if not self.dashboard_timer.isActive():
                self.dashboard_timer.start()
            self.refresh_dashboard(silent=True, force=True)
        else:
            self.dashboard_timer.stop()

    def refresh_dashboard_silent(self):
        self.refresh_dashboard(silent=True, force=True)

    def refresh_dashboard(self, silent=False, force=False):
        if not role_can_view_dashboard(self.current_role):
            return
        if self._dashboard_running:
            if force:
                self._dashboard_refresh_pending = True
            return

        if self._dashboard_thread is not None:
            try:
                if self._dashboard_thread.isRunning():
                    return
            except RuntimeError:
                # Previously deleted C++ thread object.
                self._dashboard_thread = None

        self._dashboard_running = True
        self._dashboard_silent_request = silent
        if not silent:
            self.statusBar().showMessage("Обновление дашборда...")
        self._dashboard_thread = DashboardFetchThread(self)
        self._dashboard_thread.load_ok.connect(self._on_dashboard_loaded)
        self._dashboard_thread.load_err.connect(self._on_dashboard_failed)
        self._dashboard_thread.finished.connect(self._on_dashboard_thread_finished)
        self._dashboard_thread.finished.connect(self._dashboard_thread.deleteLater)
        self._dashboard_thread.start()

    def _on_dashboard_loaded(self, stats):
        self.dashboard_labels["employees"].setText(f"Сотрудники: {stats['employees']}")
        self.dashboard_labels["franchises"].setText(f"Франшизы: {stats['franchises']}")
        self.dashboard_labels["shows"].setText(f"Показы: {stats['shows']}")
        self.dashboard_labels["customers"].setText(f"Клиенты: {stats['customers']}")
        if not self._dashboard_silent_request:
            self.statusBar().showMessage("Дашборд обновлен", 2000)

    def _on_dashboard_failed(self, error_text):
        self.statusBar().showMessage(f"Ошибка дашборда: {error_text}", 3000)

    def _on_dashboard_thread_finished(self):
        self._dashboard_running = False
        self._dashboard_thread = None
        if self._dashboard_refresh_pending:
            self._dashboard_refresh_pending = False
            self.refresh_dashboard(silent=True, force=False)

    def create_menu_actions(self):
        """Create additional menu actions that are not in the UI file"""
        # Find the Database menu (it's called "Бд" based on the retranslateUi in main_ui.py)
        db_menu = None
        for action in self.ui.menubar.actions():
            if (
                "Бд" in action.text()
                or "База" in action.text()
                or "Database" in action.text()
            ):  # Support both Russian and English
                db_menu = action.menu()
                break

        if db_menu:
            # Check if "Add" submenu already exists
            add_menu = None
            for action in db_menu.actions():
                if "Add" in action.text() or "Добавить" in action.text():
                    add_menu = action.menu()
                    break

            # If "Add" submenu doesn't exist, create it
            if not add_menu:
                add_menu = db_menu.addMenu("Add")

            # Check if "Employee" action already exists to prevent duplication
            employee_action_exists = False
            for action in add_menu.actions():
                if action.text() in {"Employee", "Сотрудник"}:
                    employee_action_exists = True
                    self.add_employee_action = action  # Reference the existing action
                    break

            # Create "Employee" action only if it doesn't already exist
            if not employee_action_exists:
                self.add_employee_action = add_menu.addAction("Сотрудник")
            else:
                self.add_employee_action.setText("Сотрудник")

            # Check if "Franchise" action already exists to prevent duplication
            franchise_action_exists = False
            for action in add_menu.actions():
                if action.text() in {"Franchise", "Франшиза"}:
                    franchise_action_exists = True
                    self.add_franchise_action = action  # Reference the existing action
                    break

            # Create "Franchise" action only if it doesn't already exist
            if not franchise_action_exists:
                self.add_franchise_action = add_menu.addAction("Франшиза")
            else:
                self.add_franchise_action.setText("Франшиза")

            self.add_dynamic_actions(add_menu)

            query_menu = None
            for action in db_menu.actions():
                if "Query" in action.text() or "Запрос" in action.text() or "Выборка" in action.text():
                    query_menu = action.menu()
                    break
            if query_menu:
                self.add_dynamic_query_actions(query_menu)

            # Check if "Remove" submenu already exists
            remove_menu = None
            for action in db_menu.actions():
                if "Remove" in action.text() or "Удалить" in action.text():
                    remove_menu = action.menu()
                    break

            # If "Remove" submenu doesn't exist, create it
            if not remove_menu:
                remove_menu = db_menu.addMenu("Remove")

            self.add_dynamic_remove_actions(remove_menu)

    def add_dynamic_actions(self, add_menu):
        """Add 'Add' menu actions for all supported database entities."""
        action_specs = [
            {
                "label": "Сотрудник",
                "title": "Добавить сотрудника",
                "query_label": "Сотрудники",
                "fields": [
                    ("username", "Логин"),
                    ("password", "Пароль"),
                    {
                        "key": "role",
                        "label": "Роль",
                        "widget": "combo",
                        "options": list(ROLE_COMBO_OPTIONS),
                    },
                ],
                "types": {"username": "str", "password": "str", "role": "str"},
                "submit": add_employee,
                "test_data": {"username": "testuser_auto", "password": "testpass123", "role": "admin"},
            },
            {
                "label": "Франшиза",
                "title": "Добавить франшизу",
                "query_label": "Франшизы",
                "fields": [
                    ("contact_person", "ФИО"),
                    ("organization", "Организация"),
                    {
                        "key": "phone",
                        "label": "Телефон",
                        "input_mask": "+0 (000) 000-00-00",
                    },
                    ("email", "Email"),
                    ("address", "Адрес"),
                    {
                        "key": "start_date",
                        "label": "Начало договора",
                        "widget": "date",
                    },
                    {
                        "key": "end_date",
                        "label": "Окончание договора",
                        "widget": "date",
                    },
                    {
                        "key": "status",
                        "label": "Статус",
                        "widget": "combo",
                        "options": [("Активна", "active"), ("Неактивна", "inactive")],
                    },
                    ("royalty_percentage", "Процент роялти"),
                    ("initial_fee", "Начальный взнос"),
                    ("monthly_fee", "Ежемесячный взнос"),
                ],
                "types": {
                    "contact_person": "str",
                    "organization": "str",
                    "phone": "str",
                    "email": "str",
                    "address": "str",
                    "start_date": "str",
                    "end_date": "str",
                    "status": "str",
                    "royalty_percentage": "float",
                    "initial_fee": "float",
                    "monthly_fee": "float",
                },
                "submit": add_franchise,
                "test_data": {
                    "contact_person": "Иванов Иван Иванович",
                    "organization": "ООО Театральная франшиза",
                    "phone": "+7 (999) 123-45-67",
                    "email": "franchise_auto@example.com",
                    "address": "г. Москва, ул. Театральная, д. 1",
                    "start_date": "2026-01-01",
                    "end_date": "2027-01-01",
                    "status": "active",
                    "royalty_percentage": "10.5",
                    "initial_fee": "100000.0",
                    "monthly_fee": "50000.0",
                },
            },
            {
                "label": "Театр",
                "title": "Добавить театр",
                "query_label": "Театры",
                "fields": [
                    {
                        "key": "contract_id",
                        "label": "Франшиза",
                        "widget": "combo",
                        "options_loader": self._franchise_options,
                    },
                    {"key": "name", "label": "Название"},
                    {"key": "location", "label": "Локация"},
                ],
                "types": {"contract_id": "int", "name": "str", "location": "str"},
                "submit": add_theater,
                "test_data": {"name": "Тестовый театр", "location": "г. Москва"},
            },
            {
                "label": "Зал",
                "title": "Добавить зал",
                "query_label": "Залы",
                "fields": [
                    {
                        "key": "theater_id",
                        "label": "Театр",
                        "widget": "combo",
                        "options_loader": self._theater_options,
                    },
                    {"key": "capacity", "label": "Вместимость"},
                ],
                "types": {"theater_id": "int", "capacity": "int"},
                "submit": add_hall,
                "test_data": {"capacity": "120"},
            },
            {
                "label": "Сценарий",
                "title": "Добавить сценарий",
                "query_label": "Сценарии",
                "fields": [("title", "Название"), ("status", "Статус"), ("description", "Описание")],
                "types": {"title": "str", "status": "str", "description": "str"},
                "submit": add_scenario,
                "test_data": {"title": "Тестовый сценарий", "status": "active", "description": "Автогенерация"},
            },
            {
                "label": "Акт",
                "title": "Добавить акт",
                "query_label": "Акты",
                "fields": [
                    {
                        "key": "scenario_id",
                        "label": "Сценарий",
                        "widget": "combo",
                        "options_loader": self._scenario_options,
                    },
                    {"key": "title", "label": "Название"},
                    {"key": "position", "label": "Позиция"},
                ],
                "types": {"scenario_id": "int", "title": "str", "position": "int"},
                "submit": add_act,
                "test_data": {"title": "Акт 1", "position": "1"},
            },
            {
                "label": "Часть",
                "title": "Добавить часть",
                "query_label": "Части",
                "fields": [
                    {
                        "key": "act_id",
                        "label": "Акт",
                        "widget": "combo",
                        "options_loader": self._act_options,
                    },
                    ("title", "Название"),
                    ("file_path", "Путь к файлу"),
                    ("position", "Позиция"),
                ],
                "types": {"act_id": "int", "title": "str", "file_path": "str", "position": "int"},
                "submit": add_part,
                "test_data": {"title": "Часть 1", "file_path": "part1.mp4", "position": "1"},
            },
            {
                "label": "Показ",
                "title": "Добавить показ",
                "query_label": "Показы",
                "fields": [
                    {
                        "key": "hall_id",
                        "label": "Зал",
                        "widget": "combo",
                        "options_loader": self._hall_options,
                    },
                    {
                        "key": "scenario_id",
                        "label": "Сценарий",
                        "widget": "combo",
                        "options_loader": self._scenario_options,
                    },
                    ("title", "Название"),
                    ("vote_type", "Тип голосования (common/vip/both)"),
                    ("duration", "Длительность (HH:MM:SS)"),
                    {
                        "key": "show_date",
                        "label": "Дата показа",
                        "widget": "datetime",
                    },
                ],
                "types": {
                    "hall_id": "int",
                    "scenario_id": "int",
                    "title": "str",
                    "vote_type": "str",
                    "duration": "str",
                    "show_date": "str",
                },
                "submit": add_show,
                "test_data": {
                    "title": "Вечерний показ",
                    "vote_type": "common",
                    "duration": "02:00:00",
                    "show_date": "2026-12-01T19:00:00",
                },
            },
            {
                "label": "Клиент",
                "title": "Добавить клиента",
                "query_label": "Клиенты",
                "fields": [
                    ("email", "Email"),
                    {
                        "key": "phone",
                        "label": "Телефон",
                        "input_mask": "+0 (000) 000-00-00",
                    },
                ],
                "types": {"email": "str", "phone": "str"},
                "submit": add_customer,
                "test_data": {"email": "customer_auto@example.com", "phone": "+7 (999) 111-22-33"},
            },
            {
                "label": "Билет",
                "title": "Добавить билет",
                "query_label": "Билеты",
                "fields": [
                    ("owner_id", "ID владельца"),
                    {
                        "key": "show_id",
                        "label": "Показ",
                        "widget": "combo",
                        "options_loader": self._show_options,
                    },
                    ("seat_number", "Место"),
                    ("price", "Цена"),
                    ("status", "Статус"),
                    ("vip_status", "VIP статус (true/false)"),
                    {
                        "key": "email",
                        "label": "Клиент",
                        "widget": "combo",
                        "options_loader": self._customer_options,
                    },
                ],
                "types": {
                    "owner_id": "int",
                    "show_id": "int",
                    "seat_number": "str",
                    "price": "float",
                    "status": "str",
                    "vip_status": "bool",
                    "email": "str",
                },
                "submit": add_ticket,
                "test_data": {
                    "owner_id": "1",
                    "seat_number": "A1",
                    "price": "1000.0",
                    "status": "available",
                    "vip_status": "false",
                },
            },
            {
                "label": "Оборудование",
                "title": "Добавить оборудование",
                "query_label": "Оборудование",
                "fields": [("name", "Название"), ("price", "Цена"), ("amount", "Количество")],
                "types": {"name": "str", "price": "float", "amount": "int"},
                "submit": add_equipment,
                "test_data": {"name": "Микрофон", "price": "5000.0", "amount": "10"},
            },
            {
                "label": "Услуга",
                "title": "Добавить услугу",
                "query_label": "Услуги",
                "fields": [("name", "Название"), ("price", "Цена"), ("amount", "Количество")],
                "types": {"name": "str", "price": "float", "amount": "int"},
                "submit": add_service,
                "test_data": {"name": "Клининг", "price": "1200.0", "amount": "3"},
            },
            {
                "label": "Аренда оборудования",
                "title": "Добавить аренду оборудования",
                "query_label": "Аренда оборудования",
                "fields": [
                    {
                        "key": "equipment_id",
                        "label": "Оборудование",
                        "widget": "combo",
                        "options_loader": self._equipment_options,
                    },
                    {
                        "key": "show_id",
                        "label": "Показ",
                        "widget": "combo",
                        "options_loader": self._show_options,
                    },
                    {
                        "key": "rent_start",
                        "label": "Начало аренды",
                        "widget": "datetime",
                    },
                    {
                        "key": "rent_end",
                        "label": "Окончание аренды",
                        "widget": "datetime",
                    },
                ],
                "types": {
                    "equipment_id": "int",
                    "show_id": "int",
                    "rent_start": "str",
                    "rent_end": "str",
                },
                "submit": add_rent_equipment,
                "test_data": {
                    "rent_start": "2026-12-01T12:00:00",
                    "rent_end": "2026-12-01T22:00:00",
                },
            },
        ]

        for spec in action_specs:
            action = None
            for existing in add_menu.actions():
                if existing.text() == spec["label"]:
                    action = existing
                    break
            if not action:
                action = add_menu.addAction(spec["label"])
            action.triggered.connect(lambda _checked=False, s=spec: self.add_entity_with_dialog(s))
            self.dynamic_add_actions.append(action)
        self._add_specs_by_label = {spec["label"]: spec for spec in action_specs}

    def add_dynamic_query_actions(self, query_menu):
        query_specs = [
            {
                "label": "Сотрудники",
                "fetch": get_all_employees,
                "columns": ["id", "username", "role", "last_online"],
                "headers": ["ID", "Логин", "Роль", "Последний онлайн"],
            },
            {
                "label": "Франшизы",
                "fetch": get_all_franchises,
                "columns": [
                    "contract_id",
                    "contact_person",
                    "organization",
                    "phone",
                    "email",
                    "address",
                    "start_date",
                    "end_date",
                    "status",
                    "royalty_percentage",
                    "initial_fee",
                    "monthly_fee",
                ],
                "headers": [
                    "ID",
                    "Контактное лицо",
                    "Организация",
                    "Телефон",
                    "Email",
                    "Адрес",
                    "Дата начала",
                    "Дата окончания",
                    "Статус",
                    "Процент роялти",
                    "Начальный взнос",
                    "Ежемесячный взнос",
                ],
            },
            {
                "label": "Театры",
                "fetch": get_all_theaters,
                "columns": ["theater_id", "contract_id", "name", "location"],
                "headers": ["ID театра", "ID договора", "Название", "Локация"],
            },
            {
                "label": "Залы",
                "fetch": get_all_halls,
                "columns": ["hall_id", "theater_id", "capacity"],
                "headers": ["ID зала", "ID театра", "Вместимость"],
            },
            {
                "label": "Сценарии",
                "fetch": get_all_scenarios,
                "columns": [
                    "scenario_id",
                    "title",
                    "status",
                    "description",
                    "created_at",
                    "tz_source_filename",
                    "tz_result_filename",
                    "tz_pipeline_status",
                ],
                "headers": [
                    "ID",
                    "Название",
                    "Статус",
                    "Описание",
                    "Создан",
                    "ТЗ (файл)",
                    "ТЗ (результат)",
                    "ТЗ (статус)",
                ],
            },
            {
                "label": "Акты",
                "fetch": get_all_acts,
                "columns": ["id", "scenario_id", "title", "position", "created_at"],
                "headers": ["ID", "ID сценария", "Название", "Позиция", "Создан"],
            },
            {
                "label": "Части",
                "fetch": get_all_parts,
                "columns": ["id", "act_id", "title", "file_path", "position", "created_at"],
                "headers": ["ID", "ID акта", "Название", "Файл", "Позиция", "Создан"],
            },
            {
                "label": "Показы",
                "fetch": get_all_shows,
                "columns": ["show_id", "hall_id", "scenario_id", "title", "vote_type", "duration", "show_date"],
                "headers": ["ID", "ID зала", "ID сценария", "Название", "Тип голос.", "Длительность", "Дата"],
            },
            {
                "label": "Клиенты",
                "fetch": get_all_customers,
                "columns": ["email", "phone"],
                "headers": ["Email", "Телефон"],
            },
            {
                "label": "Билеты",
                "fetch": get_all_tickets,
                "columns": ["ticket_id", "owner_id", "show_id", "seat_number", "price", "status", "vip_status", "email"],
                "headers": ["ID", "ID владельца", "ID показа", "Место", "Цена", "Статус", "VIP", "Email"],
            },
            {
                "label": "Оборудование",
                "fetch": get_all_equipments,
                "columns": ["equipment_id", "name", "price", "amount"],
                "headers": ["ID", "Название", "Цена", "Количество"],
            },
            {
                "label": "Услуги",
                "fetch": get_all_services,
                "columns": ["service_id", "name", "price", "amount"],
                "headers": ["ID", "Название", "Цена", "Количество"],
            },
            {
                "label": "Аренда оборудования",
                "fetch": get_all_rent_equipments,
                "columns": ["equipment_id", "show_id", "rent_start", "rent_end"],
                "headers": ["ID оборудования", "ID показа", "Начало", "Окончание"],
            },
        ]

        for action in list(query_menu.actions()):
            query_menu.removeAction(action)

        for spec in query_specs:
            action = query_menu.addAction(spec["label"])
            action.triggered.connect(lambda _checked=False, s=spec: self.show_query_table(s))
            self.dynamic_query_actions.append(action)
        self._query_specs_by_label = {spec["label"]: spec for spec in query_specs}
        self._query_to_entity = {
            "Сотрудники": "Сотрудник",
            "Франшизы": "Франшиза",
            "Театры": "Театр",
            "Залы": "Зал",
            "Сценарии": "Сценарий",
            "Акты": "Акт",
            "Части": "Часть",
            "Показы": "Показ",
            "Клиенты": "Клиент",
            "Билеты": "Билет",
            "Оборудование": "Оборудование",
            "Услуги": "Услуга",
            "Аренда оборудования": "Аренда оборудования",
        }
        self._entity_to_query = {v: k for k, v in self._query_to_entity.items()}

    def add_dynamic_remove_actions(self, remove_menu):
        remove_specs = [
            {
                "label": "Сотрудник",
                "title": "Удалить сотрудника",
                "query_label": "Сотрудники",
                "options_loader": self._employee_remove_options,
                "delete_handler": self._delete_employee,
            },
            {
                "label": "Франшиза",
                "title": "Удалить франшизу",
                "query_label": "Франшизы",
                "options_loader": self._franchise_options,
                "delete_handler": lambda contract_id: self._delete_simple("/franchises", contract_id),
            },
            {
                "label": "Театр",
                "title": "Удалить театр",
                "query_label": "Театры",
                "options_loader": self._theater_options,
                "delete_handler": lambda theater_id: self._delete_simple("/theaters", theater_id),
            },
            {
                "label": "Зал",
                "title": "Удалить зал",
                "query_label": "Залы",
                "options_loader": self._hall_options,
                "delete_handler": lambda hall_id: self._delete_simple("/halls", hall_id),
            },
            {
                "label": "Сценарий",
                "title": "Удалить сценарий",
                "query_label": "Сценарии",
                "options_loader": self._scenario_options,
                "delete_handler": lambda scenario_id: self._delete_simple("/scenarios", scenario_id),
            },
            {
                "label": "Акт",
                "title": "Удалить акт",
                "query_label": "Акты",
                "options_loader": self._act_options,
                "delete_handler": lambda act_id: self._delete_simple("/acts", act_id),
            },
            {
                "label": "Часть",
                "title": "Удалить часть",
                "query_label": "Части",
                "options_loader": self._part_options,
                "delete_handler": lambda part_id: self._delete_simple("/parts", part_id),
            },
            {
                "label": "Показ",
                "title": "Удалить показ",
                "query_label": "Показы",
                "options_loader": self._show_options,
                "delete_handler": lambda show_id: self._delete_simple("/shows", show_id),
            },
            {
                "label": "Клиент",
                "title": "Удалить клиента",
                "query_label": "Клиенты",
                "options_loader": self._customer_options,
                "delete_handler": lambda email: self._delete_simple("/customers", email),
            },
            {
                "label": "Билет",
                "title": "Удалить билет",
                "query_label": "Билеты",
                "options_loader": self._ticket_options,
                "delete_handler": lambda ticket_id: self._delete_simple("/tickets", ticket_id),
            },
            {
                "label": "Оборудование",
                "title": "Удалить оборудование",
                "query_label": "Оборудование",
                "options_loader": self._equipment_options,
                "delete_handler": lambda equipment_id: self._delete_simple("/equipments", equipment_id),
            },
            {
                "label": "Услуга",
                "title": "Удалить услугу",
                "query_label": "Услуги",
                "options_loader": self._service_options,
                "delete_handler": lambda service_id: self._delete_simple("/services", service_id),
            },
            {
                "label": "Аренда оборудования",
                "title": "Удалить аренду оборудования",
                "query_label": "Аренда оборудования",
                "options_loader": self._rent_equipment_options,
                "delete_handler": self._delete_rent_equipment,
            },
        ]

        for action in list(remove_menu.actions()):
            remove_menu.removeAction(action)

        for spec in remove_specs:
            action = remove_menu.addAction(spec["label"])
            action.triggered.connect(lambda _checked=False, s=spec: self.remove_entity_with_dialog(s))
            self.dynamic_remove_actions.append(action)
        self._remove_specs_by_label = {spec["label"]: spec for spec in remove_specs}

    def remove_entity_with_dialog(self, spec):
        if not can_delete_entity(self.current_role, spec.get("label")):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для удаления этой сущности.")
            return
        options = spec["options_loader"]()
        if not options:
            QMessageBox.information(self, "Удаление", "Нет доступных записей для удаления.")
            return

        fields = [{"key": "selected", "label": "Выберите запись", "widget": "combo", "options": options}]
        dialog = GenericAddDialog(spec["title"], fields, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        selected = dialog.get_raw_values().get("selected")
        if selected is None:
            QMessageBox.warning(self, "Ошибка", "Не выбрана запись для удаления.")
            return

        confirm_box = QMessageBox(self)
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setWindowTitle("Подтверждение удаления")
        confirm_box.setText("Вы уверены, что хотите удалить выбранную запись?")
        confirm_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_box.setDefaultButton(QMessageBox.StandardButton.No)
        yes_button = confirm_box.button(QMessageBox.StandardButton.Yes)
        no_button = confirm_box.button(QMessageBox.StandardButton.No)
        if yes_button is not None:
            yes_button.setText("Да")
        if no_button is not None:
            no_button.setText("Нет")
        button_box = confirm_box.findChild(QDialogButtonBox)
        if button_box is not None:
            button_box.setCenterButtons(True)

        if confirm_box.exec() != QMessageBox.StandardButton.Yes:
            return

        success, message = spec["delete_handler"](selected)
        if success:
            QMessageBox.information(self, "Успех", message)
            query_label = spec.get("query_label")
            if query_label and query_label in self._query_specs_by_label:
                self.invalidate_query_cache(query_label)
                self.show_query_table(self._query_specs_by_label[query_label], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def _apply_role_restrictions(self):
        """Скрыть пункты меню в соответствии с ролью (дублирует правила API для UX)."""
        if getattr(self, "_action_role_settings", None):
            self._action_role_settings.setVisible(normalize_role(self.current_role) == ROLE_ADMIN)

        for action in self.dynamic_query_actions:
            label = action.text()
            spec = self._query_specs_by_label.get(label)
            if spec and not can_open_query(self.current_role, spec["label"]):
                action.setVisible(False)
            elif spec:
                action.setVisible(True)

        for action in self.dynamic_add_actions:
            label = action.text()
            spec = self._add_specs_by_label.get(label)
            if spec and not can_mutate_entity(self.current_role, spec["label"]):
                action.setVisible(False)
            elif spec:
                action.setVisible(True)

        for action in self.dynamic_remove_actions:
            label = action.text()
            spec = self._remove_specs_by_label.get(label)
            if spec and not can_delete_entity(self.current_role, spec["label"]):
                action.setVisible(False)
            elif spec:
                action.setVisible(True)

    def _sync_quick_action_buttons(self):
        e = self._active_query_entity_label
        self.quick_add_btn.setEnabled(bool(e) and can_mutate_entity(self.current_role, e))
        self.quick_edit_btn.setEnabled(bool(e) and can_edit_entity(self.current_role, e))
        self.quick_delete_btn.setEnabled(bool(e) and can_delete_entity(self.current_role, e))
        on_scenarios = self._active_query_label == "Сценарии"
        self.quick_scenario_tz_btn.setVisible(on_scenarios)
        row = self._get_selected_row_data() if on_scenarios else None
        sid = row.get("scenario_id") if row else None
        self.quick_scenario_tz_btn.setEnabled(bool(on_scenarios and sid))

    def show_query_table(self, spec, use_cache=True):
        query_label = spec["label"]
        if not can_open_query(self.current_role, query_label):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для просмотра этой выборки.")
            return
        self._active_query_label = query_label
        self._active_query_entity_label = self._query_to_entity.get(query_label)
        self.refresh_dashboard(silent=True, force=True)

        logger.info("Выборка: %s (кэш=%s)", query_label, use_cache)

        if use_cache:
            cached = self._query_cache.get(query_label)
            if cached:
                ts = cached["ts"]
                if time.time() - ts <= self._query_cache_ttl_sec:
                    self._render_query_rows(spec, cached["rows"])
                    self.ui.db_table.setEnabled(True)
                    self.statusBar().showMessage("Показаны данные из кэша", 2000)
                    self._sync_quick_action_buttons()
                    return

        self.ui.db_table.setEnabled(False)
        self.statusBar().showMessage(f"Загрузка выборки: {query_label}...")
        logger.info("Загрузка выборки из API: %s", query_label)
        self._active_query_request_id += 1
        request_id = self._active_query_request_id

        thread = QueryFetchThread(request_id, spec["fetch"], self)
        self._query_request_specs[request_id] = spec
        thread.load_ok.connect(self._on_query_loaded)
        thread.load_err.connect(self._on_query_failed)
        thread.finished.connect(self._cleanup_finished_query_thread)
        thread.finished.connect(thread.deleteLater)

        self._query_threads[request_id] = {"thread": thread}
        thread.start()
        self._sync_quick_action_buttons()

    def _on_query_loaded(self, request_id, rows):
        if request_id != self._active_query_request_id:
            return

        spec = self._query_request_specs.get(request_id)
        if not spec:
            return

        query_label = spec["label"]
        self._query_cache[query_label] = {"rows": rows, "ts": time.time()}
        self._render_query_rows(spec, rows)
        self.ui.db_table.setEnabled(True)
        self.statusBar().showMessage(f"Загружено строк: {len(rows)}", 2500)
        logger.info("Выборка загружена: %s, строк: %s", query_label, len(rows))
        self._sync_quick_action_buttons()

    def _on_query_failed(self, request_id, error_text):
        if request_id != self._active_query_request_id:
            return
        self.ui.db_table.setEnabled(True)
        self._sync_quick_action_buttons()
        QMessageBox.warning(self, "Ошибка выборки", f"Не удалось загрузить данные: {error_text}")
        self.statusBar().showMessage("Ошибка загрузки данных", 3000)

    def _cleanup_finished_query_thread(self):
        sender_thread = self.sender()
        if sender_thread is None:
            return
        remove_key = None
        for rid, bundle in self._query_threads.items():
            if bundle["thread"] is sender_thread:
                remove_key = rid
                break
        if remove_key is not None:
            self._query_threads.pop(remove_key, None)
            self._query_request_specs.pop(remove_key, None)

    def _on_table_selection_changed(self, *_args):
        try:
            self._sync_quick_action_buttons()
        except Exception:
            logger.exception("Сбой синхронизации кнопок после смены выделения в таблице")

    def _render_query_rows(self, spec, rows):
        # Смена модели при включённой сортировке в QTableView на Windows/Qt6 даёт падения процесса.
        view = self.ui.db_table
        header = view.horizontalHeader()
        view.setSortingEnabled(False)
        try:
            old_sm = view.selectionModel()
            if old_sm is not None:
                old_sm.blockSignals(True)
        except Exception:
            pass
        try:
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        except Exception:
            pass

        view.blockSignals(True)
        try:
            view.setModel(None)
            model = GenericTableModel(rows, spec["columns"], spec["headers"])
            self._proxy_model = GlobalFilterProxyModel(self)
            self._proxy_model.setSourceModel(model)
            view.setModel(self._proxy_model)
        finally:
            view.blockSignals(False)

        sm = view.selectionModel()
        if sm is not None:
            sm.selectionChanged.connect(self._on_table_selection_changed)
        view.setSortingEnabled(True)
        header.setSortIndicatorShown(True)
        self._resize_table_columns()

    def invalidate_query_cache(self, query_label):
        self._query_cache.pop(query_label, None)

    def _on_global_search_changed(self, text):
        if self._proxy_model is None:
            return
        self._proxy_model.set_filter_text(text)

    def refresh_current_query(self):
        if not self._active_query_label:
            return
        logger.info("Обновление текущей выборки: %s", self._active_query_label)
        self.invalidate_query_cache(self._active_query_label)
        self.show_query_table(self._query_specs_by_label[self._active_query_label], use_cache=False)

    def _open_scenario_tz_dialog(self):
        if self._active_query_label != "Сценарии":
            return
        row = self._get_selected_row_data()
        if not row or row.get("scenario_id") is None:
            QMessageBox.information(self, "ТЗ сценария", "Выберите строку сценария в таблице.")
            return
        sid = int(row["scenario_id"])
        title = str(row.get("title") or "")
        dlg = ScenarioTzDialog(
            self,
            sid,
            self.current_role,
            scenario_title=title,
            on_changed=self.refresh_current_query,
        )
        dlg.exec()

    def quick_add_current_entity(self):
        if not self._active_query_entity_label:
            QMessageBox.information(self, "Быстрые действия", "Сначала откройте нужную выборку.")
            return
        if not can_mutate_entity(self.current_role, self._active_query_entity_label):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для добавления записей в этой таблице.")
            return
        spec = self._add_specs_by_label.get(self._active_query_entity_label)
        if not spec:
            QMessageBox.information(self, "Быстрые действия", "Для этой таблицы не настролено добавление.")
            return
        self.add_entity_with_dialog(spec)

    def quick_remove_current_entity(self):
        if not self._active_query_entity_label:
            QMessageBox.information(self, "Быстрые действия", "Сначала откройте нужную выборку.")
            return
        if not can_delete_entity(self.current_role, self._active_query_entity_label):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для удаления в этой таблице.")
            return
        spec = self._remove_specs_by_label.get(self._active_query_entity_label)
        if not spec:
            QMessageBox.information(self, "Быстрые действия", "Для этой таблицы не настроено удаление.")
            return
        self.remove_entity_with_dialog(spec)

    def quick_edit_current_entity(self):
        if not self._active_query_entity_label or self._active_query_label is None:
            QMessageBox.information(self, "Редактирование", "Сначала откройте нужную выборку.")
            return
        selected = self._get_selected_row_data()
        if not selected:
            QMessageBox.information(self, "Редактирование", "Выберите строку в таблице для редактирования.")
            return

        if not can_edit_entity(self.current_role, self._active_query_entity_label):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для редактирования этой таблицы.")
            return

        if self._active_query_entity_label == "Франшиза":
            self._edit_franchise(selected)
            return
        if self._active_query_entity_label == "Сотрудник":
            self._edit_employee(selected)
            return
        if self._active_query_entity_label == "Театр":
            self._edit_theater(selected)
            return
        if self._active_query_entity_label == "Зал":
            self._edit_hall(selected)
            return
        if self._active_query_entity_label == "Показ":
            self._edit_show(selected)
            return
        if self._active_query_entity_label == "Билет":
            self._edit_ticket(selected)
            return

        QMessageBox.information(
            self,
            "Редактирование",
            "Редактирование для этой таблицы пока не реализовано (доступно: сотрудники, франшизы, театры, залы, показы, билеты).",
        )

    def _get_selected_row_data(self):
        view = self.ui.db_table
        selection = view.selectionModel()
        if selection is None or not selection.hasSelection():
            return None

        selected_rows = selection.selectedRows()
        if selected_rows:
            proxy_index = selected_rows[0]
        else:
            current_index = selection.currentIndex()
            if current_index and current_index.isValid():
                proxy_index = current_index
            else:
                selected_indexes = selection.selectedIndexes()
                if not selected_indexes:
                    return None
                proxy_index = selected_indexes[0]

        source_index = self._proxy_model.mapToSource(proxy_index) if self._proxy_model else proxy_index
        source_model = self._proxy_model.sourceModel() if self._proxy_model else view.model()
        row_idx = source_index.row()
        if row_idx < 0 or row_idx >= len(source_model._rows):
            return None
        return source_model._rows[row_idx]

    def _edit_franchise(self, row):
        add_spec = self._add_specs_by_label["Франшиза"]
        resolved_fields = self._resolve_fields(add_spec)
        if resolved_fields is None:
            return
        initial_data = dict(row)
        dialog = GenericAddDialog("Редактировать франшизу", resolved_fields, initial_data=initial_data, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.get_raw_values()
        contract_id = row.get("contract_id")
        success = update_franchise(
            contract_id,
            values["contact_person"],
            values["organization"],
            values["phone"],
            values["email"],
            values["address"],
            values["start_date"],
            values["end_date"],
            values["status"],
            float(values["royalty_percentage"]),
            float(values["initial_fee"]),
            float(values["monthly_fee"]),
        )
        if success:
            QMessageBox.information(self, "Успех", "Франшиза успешно обновлена.")
            self.invalidate_query_cache("Франшизы")
            self.show_query_table(self._query_specs_by_label["Франшизы"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить франшизу.")

    def _edit_employee(self, row):
        fields = [
            ("username", "Логин"),
            {"key": "role", "label": "Роль", "widget": "combo", "options": list(ROLE_COMBO_OPTIONS)},
            ("password", "Новый пароль (необязательно)"),
        ]
        dialog = GenericAddDialog(
            "Редактировать сотрудника",
            fields,
            initial_data={"username": row.get("username"), "role": row.get("role")},
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.get_raw_values()
        success = update_employee(
            row.get("id"),
            values["username"],
            values["role"],
            values.get("password") or None,
        )
        if success:
            QMessageBox.information(self, "Успех", "Сотрудник успешно обновлен.")
            self.invalidate_query_cache("Сотрудники")
            self.show_query_table(self._query_specs_by_label["Сотрудники"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить сотрудника.")

    def _edit_theater(self, row):
        add_spec = self._add_specs_by_label["Театр"]
        resolved_fields = self._resolve_fields(add_spec)
        if resolved_fields is None:
            return
        initial_data = {
            "contract_id": row.get("contract_id"),
            "name": row.get("name") or "",
            "location": row.get("location") or "",
        }
        dialog = GenericAddDialog("Редактировать театр", resolved_fields, initial_data=initial_data, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        raw_values = dialog.get_raw_values()
        parsed_values = {}
        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")
            raw = raw_values.get(key, "")
            expected_type = add_spec["types"][key]
            if widget_type == "combo":
                parsed_values[key] = raw
                continue
            if raw == "":
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                return
            try:
                parsed_values[key] = GenericAddDialog.parse_value(raw, expected_type)
            except ValueError:
                GenericAddDialog.show_parse_error(self, label, expected_type)
                return
        theater_id = row.get("theater_id")
        success = update_theater(
            theater_id,
            parsed_values["contract_id"],
            parsed_values["name"],
            parsed_values["location"],
        )
        if success:
            QMessageBox.information(self, "Успех", "Театр успешно обновлён.")
            self.invalidate_query_cache("Театры")
            self.show_query_table(self._query_specs_by_label["Театры"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить театр.")

    def _edit_hall(self, row):
        add_spec = self._add_specs_by_label["Зал"]
        resolved_fields = self._resolve_fields(add_spec)
        if resolved_fields is None:
            return
        initial_data = {
            "theater_id": row.get("theater_id"),
            "capacity": "" if row.get("capacity") is None else str(row.get("capacity")),
        }
        dialog = GenericAddDialog("Редактировать зал", resolved_fields, initial_data=initial_data, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        raw_values = dialog.get_raw_values()
        parsed_values = {}
        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")
            raw = raw_values.get(key, "")
            expected_type = add_spec["types"][key]
            if widget_type == "combo":
                parsed_values[key] = raw
                continue
            if raw == "":
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                return
            try:
                parsed_values[key] = GenericAddDialog.parse_value(raw, expected_type)
            except ValueError:
                GenericAddDialog.show_parse_error(self, label, expected_type)
                return
        hall_id = row.get("hall_id")
        success = update_hall(hall_id, parsed_values["theater_id"], parsed_values["capacity"])
        if success:
            QMessageBox.information(self, "Успех", "Зал успешно обновлён.")
            self.invalidate_query_cache("Залы")
            self.show_query_table(self._query_specs_by_label["Залы"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить зал.")

    def _edit_show(self, row):
        add_spec = self._add_specs_by_label["Показ"]
        resolved_fields = self._resolve_fields(add_spec)
        if resolved_fields is None:
            return
        for f in resolved_fields:
            if f.get("key") == "scenario_id" and f.get("widget") == "combo":
                f["options"] = [("— нет сценария —", None)] + list(f.get("options", []))

        dur = row.get("duration")
        dur_s = "" if dur is None else str(dur).strip()

        sd = row.get("show_date")
        if sd is None:
            sd_s = ""
        else:
            sd_s = str(sd).strip()
            if " " in sd_s and "T" not in sd_s:
                sd_s = sd_s.replace(" ", "T", 1)
            if len(sd_s) >= 19:
                sd_s = sd_s[:19]

        initial_data = {
            "hall_id": row.get("hall_id"),
            "scenario_id": row.get("scenario_id"),
            "title": row.get("title") or "",
            "vote_type": row.get("vote_type") or "",
            "duration": dur_s,
            "show_date": sd_s,
        }
        dialog = GenericAddDialog("Редактировать показ", resolved_fields, initial_data=initial_data, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        raw_values = dialog.get_raw_values()
        parsed_values = {}
        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")
            raw = raw_values.get(key, "")
            expected_type = add_spec["types"][key]
            if widget_type == "combo":
                parsed_values[key] = raw
                continue
            if widget_type in ("date", "datetime"):
                if raw == "":
                    QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                    return
                parsed_values[key] = raw
                continue
            if raw == "":
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                return
            try:
                parsed_values[key] = GenericAddDialog.parse_value(raw, expected_type)
            except ValueError:
                GenericAddDialog.show_parse_error(self, label, expected_type)
                return

        show_id = row.get("show_id")
        success = update_show(
            show_id,
            parsed_values["hall_id"],
            parsed_values["scenario_id"],
            parsed_values["title"],
            parsed_values["vote_type"],
            parsed_values["duration"],
            parsed_values["show_date"],
        )
        if success:
            QMessageBox.information(self, "Успех", "Показ успешно обновлён.")
            self.invalidate_query_cache("Показы")
            self.show_query_table(self._query_specs_by_label["Показы"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить показ.")

    def _edit_ticket(self, row):
        add_spec = self._add_specs_by_label["Билет"]
        resolved_fields = self._resolve_fields(add_spec)
        if resolved_fields is None:
            return
        owner = row.get("owner_id")
        price = row.get("price")
        vip = row.get("vip_status")
        initial_data = {
            "owner_id": "" if owner is None else str(owner),
            "show_id": row.get("show_id"),
            "seat_number": row.get("seat_number") or "",
            "price": "" if price is None else str(price).strip(),
            "status": row.get("status") or "",
            "vip_status": "true" if vip else "false",
            "email": row.get("email"),
        }
        dialog = GenericAddDialog("Редактировать билет", resolved_fields, initial_data=initial_data, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        raw_values = dialog.get_raw_values()
        parsed_values = {}
        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")
            raw = raw_values.get(key, "")
            expected_type = add_spec["types"][key]

            if key == "owner_id":
                s = str(raw).strip() if raw is not None else ""
                if s == "":
                    parsed_values[key] = None
                else:
                    try:
                        parsed_values[key] = int(s)
                    except ValueError:
                        QMessageBox.warning(
                            self, "Ошибка ввода", "Поле 'ID владельца' должно быть целым числом или пустым."
                        )
                        return
                continue

            if widget_type == "combo":
                parsed_values[key] = raw
                continue

            if raw == "":
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                return
            try:
                parsed_values[key] = GenericAddDialog.parse_value(raw, expected_type)
            except ValueError:
                GenericAddDialog.show_parse_error(self, label, expected_type)
                return

        ticket_id = row.get("ticket_id")
        success = update_ticket(
            ticket_id,
            parsed_values["owner_id"],
            parsed_values["show_id"],
            parsed_values["seat_number"],
            float(parsed_values["price"]),
            parsed_values["status"],
            parsed_values["vip_status"],
            parsed_values["email"],
        )
        if success:
            QMessageBox.information(self, "Успех", "Билет успешно обновлён.")
            self.invalidate_query_cache("Билеты")
            self.show_query_table(self._query_specs_by_label["Билеты"], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить билет.")

    def _franchise_options(self):
        rows = get_all_franchises()
        return [
            (f"{row.get('organization') or 'Без названия'} (договор #{row.get('contract_id')})", row.get("contract_id"))
            for row in rows
            if row.get("contract_id") is not None
        ]

    def _theater_options(self):
        rows = get_all_theaters()
        return [
            (f"{row.get('name') or 'Без названия'} (ID {row.get('theater_id')})", row.get("theater_id"))
            for row in rows
            if row.get("theater_id") is not None
        ]

    def _scenario_options(self):
        rows = get_all_scenarios()
        return [
            (f"{row.get('title') or 'Без названия'} (ID {row.get('scenario_id')})", row.get("scenario_id"))
            for row in rows
            if row.get("scenario_id") is not None
        ]

    def _act_options(self):
        rows = get_all_acts()
        return [
            (f"{row.get('title') or 'Без названия'} (ID {row.get('id')})", row.get("id"))
            for row in rows
            if row.get("id") is not None
        ]

    def _hall_options(self):
        rows = get_all_halls()
        return [
            (f"Зал {row.get('hall_id')} (театр {row.get('theater_id')})", row.get("hall_id"))
            for row in rows
            if row.get("hall_id") is not None
        ]

    def _show_options(self):
        rows = get_all_shows()
        return [
            (f"{row.get('title') or 'Показ'} (ID {row.get('show_id')})", row.get("show_id"))
            for row in rows
            if row.get("show_id") is not None
        ]

    def _employee_remove_options(self):
        rows = get_all_employees()
        options = []
        for row in rows:
            username = row.get("username")
            emp_id = row.get("id")
            if emp_id is None or not username:
                continue
            options.append((f"{username} (ID {emp_id})", {"id": emp_id, "username": username}))
        return options

    def _part_options(self):
        rows = get_all_parts()
        return [
            (f"{row.get('title') or 'Часть'} (ID {row.get('id')})", row.get("id"))
            for row in rows
            if row.get("id") is not None
        ]

    def _ticket_options(self):
        rows = get_all_tickets()
        return [
            (f"Билет #{row.get('ticket_id')} ({row.get('seat_number') or 'без места'})", row.get("ticket_id"))
            for row in rows
            if row.get("ticket_id") is not None
        ]

    def _service_options(self):
        rows = get_all_services()
        return [
            (f"{row.get('name') or 'Услуга'} (ID {row.get('service_id')})", row.get("service_id"))
            for row in rows
            if row.get("service_id") is not None
        ]

    def _rent_equipment_options(self):
        rows = get_all_rent_equipments()
        return [
            (
                f"Оборудование {row.get('equipment_id')} / Показ {row.get('show_id')}",
                {"equipment_id": row.get("equipment_id"), "show_id": row.get("show_id")},
            )
            for row in rows
            if row.get("equipment_id") is not None and row.get("show_id") is not None
        ]

    def _delete_simple(self, endpoint, item_id):
        try:
            path = f"{endpoint.strip('/')}/{item_id}"
            response = api_delete(API_BASE_URL, path)
            if response.status_code == 200:
                return True, "Запись успешно удалена."
            return False, f"Не удалось удалить запись (код {response.status_code})."
        except RequestException as e:
            return False, f"Ошибка подключения к API: {e}"

    def _delete_employee(self, selected):
        employee_id = selected.get("id")
        username = selected.get("username")
        if username and self.current_username and username == self.current_username:
            return False, "Нельзя удалить пользователя, под которым выполнен вход."
        return self._delete_simple("/employees", employee_id)

    def _delete_rent_equipment(self, selected):
        equipment_id = selected.get("equipment_id")
        show_id = selected.get("show_id")
        try:
            response = api_delete(API_BASE_URL, f"rents_equipment/{equipment_id}/{show_id}")
            if response.status_code == 200:
                return True, "Запись успешно удалена."
            return False, f"Не удалось удалить запись (код {response.status_code})."
        except RequestException as e:
            return False, f"Ошибка подключения к API: {e}"

    def _customer_options(self):
        rows = get_all_customers()
        return [
            (f"{row.get('email')} ({row.get('phone') or 'без телефона'})", row.get("email"))
            for row in rows
            if row.get("email")
        ]

    def _equipment_options(self):
        rows = get_all_equipments()
        return [
            (f"{row.get('name') or 'Оборудование'} (ID {row.get('equipment_id')})", row.get("equipment_id"))
            for row in rows
            if row.get("equipment_id") is not None
        ]

    def _resolve_fields(self, spec):
        resolved = []
        for field in spec["fields"]:
            if isinstance(field, tuple):
                key, label = field
                resolved.append({"key": key, "label": label, "widget": "line"})
                continue

            field_copy = dict(field)
            options_loader = field_copy.pop("options_loader", None)
            if options_loader:
                options = options_loader()
                if not options:
                    QMessageBox.warning(
                        self,
                        "Недостаточно данных",
                        f"Для '{field_copy['label']}' нет доступных значений. Сначала добавьте связанные записи.",
                    )
                    return None
                field_copy["options"] = options
            resolved.append(field_copy)
        return resolved

    def add_entity_with_dialog(self, spec):
        if not can_mutate_entity(self.current_role, spec.get("label")):
            QMessageBox.warning(self, "Доступ", "Недостаточно прав для добавления этой сущности.")
            return
        resolved_fields = self._resolve_fields(spec)
        if resolved_fields is None:
            return

        dialog = GenericAddDialog(spec["title"], resolved_fields, test_data=spec.get("test_data"), parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        raw_values = dialog.get_raw_values()
        parsed_values = {}

        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            widget_type = field.get("widget", "line")
            raw = raw_values.get(key, "")
            expected_type = spec["types"][key]

            if widget_type == "combo":
                parsed_values[key] = raw
                continue

            if raw == "":
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' не может быть пустым.")
                return
            if field.get("input_mask") and "_" in str(raw):
                QMessageBox.warning(self, "Ошибка ввода", f"Поле '{label}' заполнено не полностью.")
                return

            try:
                parsed_values[key] = GenericAddDialog.parse_value(raw, expected_type)
            except ValueError:
                GenericAddDialog.show_parse_error(self, label, expected_type)
                return

        for field in resolved_fields:
            key = field["key"]
            label = field["label"]
            expected_type = spec["types"].get(key)
            val = parsed_values.get(key)
            if expected_type == "str" and isinstance(val, str) and len(val) > _MAX_STRING_FIELD_LEN:
                QMessageBox.warning(
                    self,
                    "Ошибка ввода",
                    f"Поле '{label}' слишком длинное (максимум {_MAX_STRING_FIELD_LEN} символов).",
                )
                return

        ordered_args = [parsed_values[field["key"]] for field in resolved_fields]

        # Basic date range validation for entities that have start/end dates.
        if "start_date" in parsed_values and "end_date" in parsed_values:
            if parsed_values["end_date"] < parsed_values["start_date"]:
                QMessageBox.warning(self, "Ошибка ввода", "Дата окончания не может быть раньше даты начала.")
                return
        if "rent_start" in parsed_values and "rent_end" in parsed_values:
            if parsed_values["rent_end"] < parsed_values["rent_start"]:
                QMessageBox.warning(self, "Ошибка ввода", "Окончание аренды не может быть раньше начала.")
                return

        success = spec["submit"](*ordered_args)

        if success:
            QMessageBox.information(self, "Успех", f"{spec['label']} успешно добавлен(а).")
            query_label = spec.get("query_label")
            if query_label and query_label in self._query_specs_by_label:
                self.invalidate_query_cache(query_label)
                self.show_query_table(self._query_specs_by_label[query_label], use_cache=False)
            self.refresh_dashboard(silent=True, force=True)
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить {spec['label']}. Проверьте данные и API.")

    def show_employees(self):
        self.show_query_table(
            {
                "fetch": get_all_employees,
                "columns": ["id", "username", "role", "last_online"],
                "headers": ["ID", "Логин", "Роль", "Последний онлайн"],
            }
        )

    def show_franchises(self):
        self.show_query_table(
            {
                "fetch": get_all_franchises,
                "columns": [
                    "contract_id",
                    "contact_person",
                    "organization",
                    "phone",
                    "email",
                    "address",
                    "start_date",
                    "end_date",
                    "status",
                    "royalty_percentage",
                    "initial_fee",
                    "monthly_fee",
                ],
                "headers": [
                    "ID",
                    "Контактное лицо",
                    "Организация",
                    "Телефон",
                    "Email",
                    "Адрес",
                    "Дата начала",
                    "Дата окончания",
                    "Статус",
                    "Процент роялти",
                    "Начальный взнос",
                    "Ежемесячный взнос",
                ],
            }
        )

    def _resize_table_columns(self):
        header = self.ui.db_table.horizontalHeader()
        model = header.model()
        if model is None:
            return
        n = model.columnCount()
        if n <= 0:
            return
        font_metrics = header.fontMetrics()
        for col in range(n):
            raw = model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            text_width = font_metrics.horizontalAdvance(str(raw if raw is not None else ""))
            adjusted_width = max(text_width + 20, 100)
            header.resizeSection(col, adjusted_width)
        self.ui.db_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        header.setStretchLastSection(True)
