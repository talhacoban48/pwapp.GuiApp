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
    QAction,
    QApplication,
    QMessageBox,
    QFileDialog,
    QCheckBox,
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRect
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
        self.setWindowIcon(QIcon(get_resource_path("assets/Password.ico")))

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

    @staticmethod
    def _make_copy_icon() -> QIcon:
        px = QPixmap(16, 16)
        px.fill(Qt.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#8b97b8"))
        pen.setWidthF(1.3)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRect(1, 4, 8, 9))   # back page
        p.drawRect(QRect(5, 1, 8, 9))   # front page
        p.end()
        return QIcon(px)

    def _add_copy_action(self, field: QLineEdit):
        action = QAction(self._make_copy_icon(), "", field)
        action.setToolTip("Copy")
        action.triggered.connect(
            lambda: QApplication.clipboard().setText(field.text())
        )
        field.addAction(action, QLineEdit.TrailingPosition)

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

        # Left panel
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
        for f in (self.app_name_field, self.username_field,
                  self.email_field, self.password_field):
            self._add_copy_action(f)

        self.url_field = QTextEdit()
        self.url_field.setMinimumWidth(275)
        self.url_field.setMaximumWidth(420)
        self.url_field.setMaximumHeight(150)

        self.url_copy_btn = QPushButton("⎘")
        self.url_copy_btn.setFixedSize(26, 26)
        self.url_copy_btn.setToolTip("Copy URL")
        self.url_copy_btn.setObjectName("urlCopyBtn")
        self.url_copy_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(
                self.url_field.toPlainText()
            )
        )

        # Active / Passive toggle
        self.status_cb = QCheckBox()
        self.status_cb.setChecked(True)
        self.status_cb.clicked.connect(self._on_status_toggled)

        self.status_label = QLabel("Active")

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

    def _build_layout(self):
        # --- Left group -----------------------------------------------
        left_group = QGroupBox("Apps / Sites")
        left_group.setObjectName("leftPanel")

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.entries_list)
        left_group.setLayout(left_layout)

        # --- Right group ----------------------------------------------
        right_group = QGroupBox("Entry Details")
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

        right_layout.addStretch()
        right_layout.addLayout(make_field_row("App Name :",  self.app_name_field))
        right_layout.addLayout(make_field_row("User Name :", self.username_field))
        right_layout.addLayout(make_field_row("Email :",     self.email_field))
        right_layout.addLayout(make_field_row("Password :",  self.password_field))
        right_layout.addLayout(make_field_row("URL :",       self.url_field, self.url_copy_btn))
        right_layout.addLayout(make_field_row("Status :",    self.status_cb, self.status_label))
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

    def _refresh_list(self):
        self.entries_list.clear()
        rows = self.db.get_all()
        names = [
            "   " + name
            for name, status in rows
            if self.show_passive or status
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

    def _clear_fields(self):
        for field in (self.app_name_field, self.username_field,
                      self.email_field, self.password_field,
                      self.generated_field):
            field.clear()
        self.url_field.clear()
        self.status_cb.setChecked(True)
        self.status_label.setText("Active")

    def _populate_fields(self, entry: dict):
        self.app_name_field.setText(entry.get("appname") or "")
        self.username_field.setText(entry.get("username") or "")
        self.email_field.setText(entry.get("email") or "")
        self.password_field.setText(entry.get("password") or "")
        self.url_field.setText(entry.get("url") or "")
        is_active = entry.get("recordStatus", True)
        self.status_cb.setChecked(is_active)
        self.status_label.setText("Active" if is_active else "Passive")

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
