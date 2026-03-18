import locale

import pandas as pd
from PyQt5.QtWidgets import (
    QMainWindow,
    QListWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QMessageBox,
    QFileDialog,
    QCheckBox,
)
from PyQt5.QtGui import QIcon, QFont

from database.db_manager import DatabaseManager
from utils.password_gen import generate_password
from utils.resources import get_resource_path
from ui.widgets import make_field_row


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.db = DatabaseManager()
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

        file_menu = bar.addMenu("File")
        file_menu.addAction("Save as Excel")
        file_menu.addAction("Save as CSV")
        file_menu.triggered.connect(self._on_export)

        import_menu = bar.addMenu("Import")
        import_menu.addAction("Import Excel")
        import_menu.addAction("Import CSV")
        import_menu.triggered.connect(self._on_import)

    # ------------------------------------------------------------------ #
    #  Widgets                                                             #
    # ------------------------------------------------------------------ #

    def _build_widgets(self):
        font = QFont("Times", 10)

        def _line_edit(min_w=275, min_h=40) -> QLineEdit:
            w = QLineEdit()
            w.setFont(font)
            w.setMinimumWidth(min_w)
            w.setMinimumHeight(min_h)
            return w

        def _button(text: str, handler, min_w=100, min_h=40) -> QPushButton:
            b = QPushButton(text)
            b.setFont(font)
            b.setMinimumWidth(min_w)
            b.setMinimumHeight(min_h)
            b.clicked.connect(handler)
            return b

        # Left panel
        self.show_passive_cb = QCheckBox("Show passive entries")
        self.show_passive_cb.setFont(QFont("Times", 11))
        self.show_passive_cb.clicked.connect(self._on_toggle_passive)

        self.entries_list = QListWidget()
        self.entries_list.setMinimumHeight(500)
        self.entries_list.setMinimumWidth(200)
        self.entries_list.setFont(QFont("Times", 11))
        self.entries_list.mouseDoubleClickEvent = self._on_open_entry

        # Right panel — input fields
        self.app_name_field = _line_edit()
        self.username_field = _line_edit()
        self.email_field    = _line_edit()
        self.password_field = _line_edit()

        self.url_field = QTextEdit()
        self.url_field.setFont(font)
        self.url_field.setMinimumWidth(275)
        self.url_field.setMaximumHeight(120)

        # Active / Passive toggle
        self.status_cb = QCheckBox()
        self.status_cb.setFont(font)
        self.status_cb.setChecked(True)
        self.status_cb.clicked.connect(self._on_status_toggled)

        self.status_label = QLabel("Active")
        self.status_label.setFont(font)

        # Action buttons
        self.clear_btn  = _button("Clear",  self._on_clear)
        self.insert_btn = _button("Insert", self._on_insert)
        self.update_btn = _button("Update", self._on_update)
        self.delete_btn = _button("Delete", self._on_delete)

        # Password generator
        self.gen_btn         = _button("Generate Password", self._on_generate_password)
        self.generated_field = _line_edit()

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    def _build_layout(self):
        # --- Left group -----------------------------------------------
        left_group = QGroupBox("Apps / Sites")

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(self.show_passive_cb)
        top_bar.addStretch()

        left_layout = QVBoxLayout()
        left_layout.addStretch()
        left_layout.addLayout(top_bar)
        left_layout.addWidget(self.entries_list)
        left_layout.addStretch()
        left_group.setLayout(left_layout)

        # --- Right group ----------------------------------------------
        right_group = QGroupBox("Entry Details")
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
        right_layout.addLayout(make_field_row("URL :",       self.url_field))
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

        container = QGroupBox()
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
            if self.show_passive or status == "aktif"
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
            "aktifpasif": "aktif" if self.status_cb.isChecked() else "pasif",
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
        is_active = entry.get("aktifpasif") == "aktif"
        self.status_cb.setChecked(is_active)
        self.status_label.setText("Active" if is_active else "Passive")

    # ------------------------------------------------------------------ #
    #  Slots — list interaction                                            #
    # ------------------------------------------------------------------ #

    def _on_toggle_passive(self):
        self.show_passive = self.show_passive_cb.isChecked()
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
            f"  Status   : {data['aktifpasif']}",
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
        if data["aktifpasif"] == "pasif" and not self.show_passive_cb.isChecked():
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
            f"  Status   : {data['aktifpasif']}",
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
        if data["aktifpasif"] == "pasif" and not self.show_passive_cb.isChecked():
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

    def _on_export(self, action):
        text = action.text()
        if text == "Save as Excel":
            path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "Excel (*.xlsx)"
            )
            if path:
                try:
                    self.db.export_to_excel(path)
                    QMessageBox.information(self, "Success", "Exported to Excel.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

        elif text == "Save as CSV":
            path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "CSV (*.csv)"
            )
            if path:
                try:
                    self.db.export_to_csv(path)
                    QMessageBox.information(self, "Success", "Exported to CSV.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _on_import(self, action):
        text = action.text()
        df = None

        if text == "Import Excel":
            path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "Excel (*.xlsx)"
            )
            if path:
                try:
                    df = pd.read_excel(path)
                except Exception as e:
                    QMessageBox.critical(self, "Error",
                                         f"Could not read file:\n{e}")
                    return

        elif text == "Import CSV":
            path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "CSV (*.csv)"
            )
            if path:
                try:
                    df = pd.read_csv(path)
                except Exception as e:
                    QMessageBox.critical(self, "Error",
                                         f"Could not read file:\n{e}")
                    return

        if df is None:
            return

        try:
            inserted, skipped = self.db.import_from_dataframe(df)
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed:\n{e}")
            return

        self._refresh_list()
        msg = f"{inserted} entries imported."
        if skipped:
            msg += f"\n{skipped} entries skipped (already exist or invalid)."
        QMessageBox.information(self, "Success", msg)
