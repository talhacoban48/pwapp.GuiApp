import csv
import locale

import openpyxl
from PyQt5.QtWidgets import (
    QMainWindow,
    QListWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QWidget,
    QApplication,
    QMessageBox,
    QFileDialog,
    QCheckBox,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QAction
from cryptography.fernet import Fernet

from database.db_manager import DatabaseManager
from utils.auth_manager import AuthManager
from utils.password_gen import generate_password
from utils.resources import get_resource_path
from ui.widgets import make_field_row
from ui.change_password_dialog import ChangePasswordDialog


class MainWindow(QMainWindow):

    def __init__(self, fernet: Fernet, auth_manager: AuthManager,
                 first_run: bool = False):
        super().__init__()

        self.auth_manager = auth_manager
        self.db = DatabaseManager(fernet=fernet)
        if first_run:
            self.db.migrate_to_encrypted()
        self.show_passive = False

        self.setWindowTitle("Password Manager")
        self.setGeometry(400, 200, 960, 648)
        self.setWindowIcon(QIcon(get_resource_path("assets/favicon.ico")))

        self._build_menubar()
        self._build_widgets()
        self._build_layout()
        self._refresh_list()
        self.show()

    # ------------------------------------------------------------------ #
    #  Menu bar                                                            #
    # ------------------------------------------------------------------ #

    def _build_menubar(self):
        bar = self.menuBar()

        # File — export & import
        file_menu = bar.addMenu("File")

        act = file_menu.addAction("Save as Excel")
        act.setShortcut("Ctrl+E")
        act.triggered.connect(self._export_excel)

        act = file_menu.addAction("Save as CSV")
        act.setShortcut("Ctrl+Shift+E")
        act.triggered.connect(self._export_csv)

        file_menu.addSeparator()

        act = file_menu.addAction("Import Excel")
        act.setShortcut("Ctrl+I")
        act.triggered.connect(self._import_excel)

        act = file_menu.addAction("Import CSV")
        act.setShortcut("Ctrl+Shift+I")
        act.triggered.connect(self._import_csv)

        # Settings
        settings_menu = bar.addMenu("Settings")

        self.show_passive_action = settings_menu.addAction("Show Passive Entries")
        self.show_passive_action.setCheckable(True)
        self.show_passive_action.setChecked(False)
        self.show_passive_action.triggered.connect(self._on_toggle_passive)

        settings_menu.addSeparator()
        settings_menu.addAction("Change Master Password").triggered.connect(
            self._on_change_password
        )

        # Help
        help_menu = bar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(self._show_about)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _make_copy_btn(self, field) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(QIcon(get_resource_path("assets/copy.ico")))
        btn.setIconSize(QSize(16, 16))
        btn.setFixedSize(26, 26)
        btn.setToolTip("Copy")
        btn.setObjectName("copyBtn")
        is_text_edit = isinstance(field, QTextEdit)
        btn.clicked.connect(
            lambda: QApplication.clipboard().setText(
                field.toPlainText() if is_text_edit else field.text()
            )
        )
        return btn

    # ------------------------------------------------------------------ #
    #  Widgets                                                             #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):

        def _line_edit(min_w=275, max_w=420, min_h=38) -> QLineEdit:
            w = QLineEdit()
            w.setMinimumWidth(min_w)
            w.setMaximumWidth(max_w)
            w.setMinimumHeight(min_h)
            return w

        def _button(text: str, handler, min_w=100, min_h=38) -> QPushButton:
            b = QPushButton(text)
            b.setMinimumWidth(min_w)
            b.setMinimumHeight(min_h)
            b.clicked.connect(handler)
            return b

        # Left panel — search
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search…")
        self.search_field.setMinimumHeight(34)
        self.search_field.addAction(
            QAction(QIcon(get_resource_path("assets/search.ico")), "", self.search_field),
            QLineEdit.LeadingPosition,
        )
        self.search_field.textChanged.connect(self._on_search_changed)

        self.cancel_search_btn = QPushButton()
        self.cancel_search_btn.setIcon(QIcon(get_resource_path("assets/cancel.ico")))
        self.cancel_search_btn.setIconSize(QSize(14, 14))
        self.cancel_search_btn.setFixedSize(34, 34)
        self.cancel_search_btn.setToolTip("Clear search")
        self.cancel_search_btn.setObjectName("cancelSearchBtn")
        self.cancel_search_btn.setVisible(False)
        self.cancel_search_btn.clicked.connect(self.search_field.clear)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(500)
        self._search_timer.timeout.connect(self._refresh_list)

        # Left panel — list
        self.entries_list = QListWidget()
        self.entries_list.setMinimumHeight(200)
        self.entries_list.setMinimumWidth(200)
        self.entries_list.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.entries_list.mouseDoubleClickEvent = self._on_open_entry

        # Right panel — input fields
        self.app_name_field = _line_edit()
        self.username_field = _line_edit()
        self.email_field    = _line_edit()
        self.password_field = _line_edit()

        self.url_field = QTextEdit()
        self.url_field.setMinimumWidth(275)
        self.url_field.setMaximumWidth(420)
        self.url_field.setMaximumHeight(150)

        self.app_name_copy_btn = self._make_copy_btn(self.app_name_field)
        self.username_copy_btn = self._make_copy_btn(self.username_field)
        self.email_copy_btn    = self._make_copy_btn(self.email_field)
        self.password_copy_btn = self._make_copy_btn(self.password_field)
        self.url_copy_btn      = self._make_copy_btn(self.url_field)

        # Active / Passive toggle
        self.status_cb = QCheckBox()
        self.status_cb.setChecked(True)
        self.status_cb.clicked.connect(self._on_status_toggled)

        self.status_label = QLabel("Active")

        # Date info labels (read-only)
        self.created_date_lbl = QLabel("—")
        self.created_date_lbl.setObjectName("dateLabel")
        self.updated_date_lbl = QLabel("—")
        self.updated_date_lbl.setObjectName("dateLabel")

        # Action buttons
        self.clear_btn  = _button("Clear",  self._on_clear)
        self.insert_btn = _button("Insert", self._on_insert)
        self.update_btn = _button("Update", self._on_update)
        self.delete_btn = _button("Delete", self._on_delete)
        self.clear_btn.setProperty("role", "clear")
        self.insert_btn.setProperty("role", "insert")
        self.update_btn.setProperty("role", "update")
        self.delete_btn.setProperty("role", "delete")

        # Password generator
        self.gen_btn         = _button("Generate", self._on_generate_password)
        self.generated_field = _line_edit()
        self.gen_btn.setProperty("role", "generate")

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _panel_header(icon_path: str, title: str, object_name: str) -> QHBoxLayout:
        icon_lbl = QLabel()
        icon_lbl.setPixmap(
            QIcon(get_resource_path(icon_path)).pixmap(16, 16)
        )
        title_lbl = QLabel(title)
        title_lbl.setObjectName(object_name)
        row = QHBoxLayout()
        row.setContentsMargins(4, 0, 0, 4)
        row.setSpacing(6)
        row.addWidget(icon_lbl)
        row.addWidget(title_lbl)
        row.addStretch()
        return row

    def _build_layout(self):
        # --- Left group -----------------------------------------------
        left_group = QGroupBox()
        left_group.setObjectName("leftPanel")

        search_row = QHBoxLayout()
        search_row.setSpacing(4)
        search_row.addWidget(self.search_field)
        search_row.addWidget(self.cancel_search_btn)

        left_layout = QVBoxLayout()
        left_layout.addLayout(
            self._panel_header("assets/apps.ico", "Apps / Sites", "leftPanelTitle")
        )
        left_layout.addLayout(search_row)
        left_layout.addWidget(self.entries_list)
        left_group.setLayout(left_layout)

        # --- Right group ----------------------------------------------
        right_group = QGroupBox()
        right_group.setObjectName("rightPanel")
        right_layout = QVBoxLayout()

        button_row = QHBoxLayout()
        button_row.addStretch()
        for btn in (self.clear_btn, self.insert_btn,
                    self.update_btn, self.delete_btn):
            button_row.addWidget(btn)
        button_row.addStretch()

        gen_row = QHBoxLayout()
        gen_row.addStretch()
        gen_row.addWidget(self.gen_btn)
        gen_row.addStretch()

        gen_field_row = QHBoxLayout()
        gen_field_row.addStretch()
        gen_field_row.addWidget(self.generated_field)
        gen_field_row.addStretch()

        right_layout.addLayout(
            self._panel_header("assets/detail.ico", "Entry Details", "rightPanelTitle")
        )
        right_layout.addStretch()
        right_layout.addLayout(make_field_row("App Name :",  self.app_name_field, self.app_name_copy_btn))
        right_layout.addLayout(make_field_row("User Name :", self.username_field, self.username_copy_btn))
        right_layout.addLayout(make_field_row("Email :",     self.email_field,    self.email_copy_btn))
        right_layout.addLayout(make_field_row("Password :",  self.password_field, self.password_copy_btn))
        right_layout.addLayout(make_field_row("Extra Information :",       self.url_field,      self.url_copy_btn))
        right_layout.addLayout(make_field_row("Status :",    self.status_cb, self.status_label))
        right_layout.addSpacing(8)
        right_layout.addLayout(make_field_row("Created :",   self.created_date_lbl))
        right_layout.addLayout(make_field_row("Updated :",   self.updated_date_lbl))
        right_layout.addSpacing(20)
        right_layout.addLayout(button_row)
        right_layout.addSpacing(10)
        right_layout.addLayout(gen_row)
        right_layout.addLayout(gen_field_row)
        right_layout.addStretch()
        right_group.setLayout(right_layout)

        # --- Main layout ----------------------------------------------
        main_layout = QHBoxLayout()
        main_layout.addWidget(left_group, 45)
        main_layout.addWidget(right_group, 55)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _on_search_changed(self, text: str):
        self.cancel_search_btn.setVisible(bool(text))
        self._search_timer.start()

    def _refresh_list(self):
        self.entries_list.clear()
        query = self.search_field.text().lower() if hasattr(self, "search_field") else ""
        rows = self.db.get_all()
        names = [
            "   " + name
            for name, status in rows
            if (self.show_passive or status) and query in name.lower()
        ]
        try:
            names.sort(key=locale.strxfrm)
        except Exception:
            names.sort()
        self.entries_list.addItems(names)

    def _read_fields(self) -> dict:
        return {
            "appname":    self.app_name_field.text().strip(),
            "username":   self.username_field.text().strip(),
            "email":      self.email_field.text().strip(),
            "password":   self.password_field.text().strip(),
            "url":        self.url_field.toPlainText().strip(),
            "recordStatus": self.status_cb.isChecked(),
        }

    @staticmethod
    def _fmt_date(value: str | None) -> str:
        if not value:
            return "—"
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(value)
            return dt.strftime("%d %b %Y,  %H:%M")
        except Exception:
            return value

    def _clear_fields(self):
        for field in (self.app_name_field, self.username_field,
                      self.email_field, self.password_field,
                      self.generated_field):
            field.clear()
        self.url_field.clear()
        self.status_cb.setChecked(True)
        self.status_label.setText("Active")
        self.created_date_lbl.setText("—")
        self.updated_date_lbl.setText("—")

    def _populate_fields(self, entry: dict):
        self.app_name_field.setText(entry.get("appname") or "")
        self.username_field.setText(entry.get("username") or "")
        self.email_field.setText(entry.get("email") or "")
        self.password_field.setText(entry.get("password") or "")
        self.url_field.setText(entry.get("url") or "")
        is_active = entry.get("recordStatus", True)
        self.status_cb.setChecked(is_active)
        self.status_label.setText("Active" if is_active else "Passive")
        self.created_date_lbl.setText(self._fmt_date(entry.get("createdDate")))
        self.updated_date_lbl.setText(self._fmt_date(entry.get("updatedDate")))

    # ------------------------------------------------------------------ #
    #  Slots — list interaction                                            #
    # ------------------------------------------------------------------ #

    def _on_toggle_passive(self):
        self.show_passive = self.show_passive_action.isChecked()
        self._refresh_list()

    def _on_open_entry(self, event):
        item = self.entries_list.currentItem()
        if item is None:
            return
        appname = item.text().strip()
        entry = self.db.get_one(appname)
        if entry:
            self._populate_fields(entry)

    # ------------------------------------------------------------------ #
    #  Slots — CRUD                                                        #
    # ------------------------------------------------------------------ #

    def _on_clear(self):
        self._clear_fields()

    def _on_insert(self):
        data = self._read_fields()
        if not data["appname"] or not data["password"]:
            QMessageBox.warning(self, "Warning", "App name and password are required.")
            return

        if self.db.exists(data["appname"]):
            QMessageBox.warning(self, "Warning",
                                f"'{data['appname']}' already exists.")
            return

        answer = QMessageBox.question(
            self, "Confirm Insert",
            f"Insert new entry for '{data['appname']}'?\n\n"
            f"  Username : {data['username']}\n"
            f"  Email    : {data['email']}\n"
            f"  Password : {data['password']}\n"
            f"  URL      : {data['url']}\n"
            f"  Status   : {'Active' if data['recordStatus'] else 'Passive'}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.insert(**data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Insert failed:\n{e}")
            return

        self._refresh_list()
        if not data["recordStatus"] and not self.show_passive_action.isChecked():
            self._clear_fields()
        QMessageBox.information(self, "Success", "Entry added successfully.")

    def _on_update(self):
        data = self._read_fields()
        if not data["appname"] or not data["password"]:
            QMessageBox.warning(self, "Warning", "App name and password are required.")
            return

        if not self.db.exists(data["appname"]):
            QMessageBox.warning(self, "Warning",
                                f"'{data['appname']}' does not exist.")
            return

        answer = QMessageBox.question(
            self, "Confirm Update",
            f"Update '{data['appname']}' with the following values?\n\n"
            f"  Username : {data['username']}\n"
            f"  Email    : {data['email']}\n"
            f"  Password : {data['password']}\n"
            f"  URL      : {data['url']}\n"
            f"  Status   : {'Active' if data['recordStatus'] else 'Passive'}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.update(**data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed:\n{e}")
            return

        self._refresh_list()
        if not data["recordStatus"] and not self.show_passive_action.isChecked():
            self._clear_fields()
        QMessageBox.information(self, "Success", "Entry updated successfully.")

    def _on_delete(self):
        appname = self.app_name_field.text().strip()
        if not appname:
            QMessageBox.warning(self, "Warning", "App name is required.")
            return

        if not self.db.exists(appname):
            QMessageBox.warning(self, "Warning",
                                f"'{appname}' does not exist.")
            return

        answer = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{appname}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.db.delete(appname)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Delete failed:\n{e}")
            return

        self._refresh_list()
        self._clear_fields()
        QMessageBox.information(self, "Success", "Entry deleted.")

    # ------------------------------------------------------------------ #
    #  Slots — password generator                                          #
    # ------------------------------------------------------------------ #

    def _on_generate_password(self):
        self.generated_field.setText(generate_password())

    def _on_status_toggled(self):
        self.status_label.setText(
            "Active" if self.status_cb.isChecked() else "Passive"
        )

    # ------------------------------------------------------------------ #
    #  Slots — export / import                                             #
    # ------------------------------------------------------------------ #

    def _export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel (*.xlsx)")
        if path:
            try:
                self.db.export_to_excel(path)
                QMessageBox.information(self, "Success", "Exported to Excel.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV (*.csv)")
        if path:
            try:
                self.db.export_to_csv(path)
                QMessageBox.information(self, "Success", "Exported to CSV.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel (*.xlsx)")
        if path:
            try:
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ws = wb.active
                rows_iter = ws.iter_rows(values_only=True)
                headers = [str(c) for c in next(rows_iter)]
                rows = [dict(zip(headers, row)) for row in rows_iter]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")
                return
            self._do_import(rows)

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV (*.csv)")
        if path:
            try:
                with open(path, newline="", encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")
                return
            self._do_import(rows)

    def _do_import(self, rows):

        try:
            inserted, updated, skipped = self.db.import_from_rows(rows)
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")
            return

        self._refresh_list()
        parts = []
        if inserted:
            parts.append(f"{inserted} new entries added.")
        if updated:
            parts.append(f"{updated} entries updated (imported data was newer).")
        if skipped:
            parts.append(f"{skipped} entries skipped (up-to-date or no date to compare).")
        if not parts:
            parts.append("No changes made.")
        QMessageBox.information(self, "Import Complete", "\n".join(parts))

    # ------------------------------------------------------------------ #
    #  Slots — settings & help                                            #
    # ------------------------------------------------------------------ #

    def _on_change_password(self):
        dialog = ChangePasswordDialog(self.auth_manager, parent=self)
        if dialog.exec_() != dialog.Accepted:
            return
        try:
            new_fernet, pending_config = self.auth_manager.prepare_new_key(
                dialog.new_password
            )
            self.db.rekey(new_fernet)
            self.auth_manager.commit_key(pending_config)
            QMessageBox.information(self, "Success",
                                    "Master password changed successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Failed to change master password:\n{e}")

    def _show_about(self):
        QMessageBox.about(
            self, "About Password Manager",
            "Password Manager v1.0\n\n"
            "Local password manager with AES-256 encryption.\n"
            "Your data never leaves your machine.",
        )
